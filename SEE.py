import math
from io import StringIO

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Google Sheet–driven product profiles
#
# The app reads product profiles (vapor pressure, vapor molecular weight and
# vapor-component weight %) from a public Google Sheet. Add a new product by
# adding a row to the sheet; no code changes needed. The app re-checks the
# sheet every 10 minutes (or click "Reload profiles now" in the sidebar).
# ---------------------------------------------------------------------------
SHEET_EXPORT_URL = (
    "https://docs.google.com/spreadsheets/d/1duewVkxON4m83aXbcMZcwRRygz9AtkYRPNBDRT5_F_g/"
    "export?format=csv&gid=0"
)
SHEET_LINK = (
    "https://docs.google.com/spreadsheets/d/1duewVkxON4m83aXbcMZcwRRygz9AtkYRPNBDRT5_F_g/"
    "edit#gid=0"
)

# Bundled copy of the profile sheet so the app keeps working offline / if the
# sheet is temporarily unreachable. Keep in sync with the sheet.
FALLBACK_CSV = (
    "Product Name,Product Vapor Pressure (PSI),Product Vapor Molecular Weight (g/mol),"
    "weight% of Vapor Components ->,Benzene,Ethylbenzene,Hexane,Isooctane,Toluene,Xylene,"
    'Naphthalene,"1,2,4-Trimethylbenzene",Pentane,Butane,H2S\r\n'
    'Gasoline,7,68,"From Table 3-1 from API Publication 1673 (May 1998), and Mr. James '
    "Durham of the EPA\",0.6,0.5,1.56,0.1,1,1.4,0.218,0.015,3.8,2,0.5\r\n"
    "WTI Crude,9,50,filler for testing,0.6,0.5,1.56,0.1,1,1.4,0.218,0.015,3.8,2,0.5\r\n"
    "Diesel Fuel,0.01,130,filler for testing,0.6,0.5,1.56,0.1,1,1.4,0.218,0.015,3.8,2,0.5\r\n"
)

# Method 3 (Empirical) evaporation equations, from Merv Fingas "The Evaporation
# of Oil Spills" Table 7.2. Keyed by the exact product name used in the sheet.
# El (lb evaporated per gallon) = (a + b * T_C) * f(T_minutes) * density / 100
# where f() is "ln" or "sqrt". Products without an entry have no Method 3.
EMPIRICAL = {
    "Gasoline": {"a": 13.2, "b": 0.21, "f": "ln", "density": 6.07},
    "WTI Crude": {"a": 3.08, "b": 0.045, "f": "ln", "density": 7.21},
    "Diesel Fuel": {"a": 0.39, "b": 0.013, "f": "sqrt", "density": 7.1},
}


# ---------------------------------------------------------------------------
# Pure logic (no Streamlit calls, so it is unit-testable)
# ---------------------------------------------------------------------------
def _to_float(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def parse_products_csv(csv_text):
    """Parse the product-profile CSV from the Google Sheet export.

    Expected layout (from the sheet template):
        Product Name | Vapor Pressure (PSI) | Vapor MW (g/mol) | <note column> | <component weight % columns...>

    Everything to the right of the note column ("weight% of Vapor Components ->")
    is treated as a vapor component; the app can also carry extra components
    the user adds as new columns.
    """
    df = pd.read_csv(StringIO(csv_text))
    comp_start = 4
    for i, col in enumerate(df.columns):
        if "weight%" in str(col) or "Vapor Components" in str(col):
            comp_start = i + 1
            break
    component_cols = list(df.columns[comp_start:])

    products = []
    for _, row in df.iterrows():
        name = str(row.iloc[0]).strip()
        if not name or name.lower() == "nan":
            continue
        components = {}
        for col in component_cols:
            w = _to_float(row[col])
            if w is not None:
                components[str(col).strip()] = w
        note = ""
        if len(df.columns) > comp_start - 1:
            note = str(row.iloc[comp_start - 1]).strip()
            if note.lower() == "nan":
                note = ""
        products.append(
            {
                "name": name,
                "vp_psi": _to_float(row.iloc[1]),
                "mw": _to_float(row.iloc[2]),
                "note": note,
                "components": components,
            }
        )
    return products


@st.cache_data(ttl=600, show_spinner="Loading product profiles from Google Sheet...")
def load_products():
    """Fetch product profiles from the Google Sheet (fallback to bundled copy)."""
    source = "Google Sheet"
    try:
        r = requests.get(SHEET_EXPORT_URL, timeout=15)
        r.raise_for_status()
        csv_text = r.text
    except Exception:
        csv_text = FALLBACK_CSV
        source = "bundled fallback (Google Sheet unreachable)"
    return parse_products_csv(csv_text), source


# RMP Guidance Equation D-1:
# Qr = Evaporation rate (lb/min); U = wind speed (m/s); MW = molecular weight;
# A = pool surface area (ft^2); VP = vapor pressure (mm Hg); T = temperature (K)
def RMP_equation(U, MW, A, VP, T):
    return 0.284 * (U**0.78) * (MW ** (2 / 3)) * A * VP / (82.05 * T)


def mph_mps(S):
    return S / 2.237


def psi_mmhg(P):
    return 51.751 * P


def FtK(F):
    return (F - 32) * 5 / 9 + 273.15


def FtC(F):
    return (F - 32) * 5 / 9


# EPA EIIP Volume II Chapter 16 Eq. 3-24 (open-top vessel / spill evaporation)
def EIIPCh16(Mi, Ki, A, Pisat, Tl):
    return Mi * Ki * A * Pisat / (998.9 * Tl)


def Ki(Mi):
    return 0.83 * ((18.02 / Mi) ** (1 / 3)) * 118.1102


def empirical_el(name, F, T):
    """lb evaporated per gallon for Method 3; None when no equation exists."""
    eq = EMPIRICAL.get(name)
    if eq is None or T is None or T <= 0:
        return None
    C = FtC(F)
    ft = math.log(T) if eq["f"] == "ln" else math.sqrt(T)
    return (eq["a"] + eq["b"] * C) * ft * eq["density"] / 100.0


def speciation_rows(total_lb, components):
    """Component breakdown table for one method total (pounds).

    Component pounds = total x component weight % / 100. The profile's weight %
    usually does not sum to 100, so a final "Other / uncharacterized" row makes
    the table add up to the method total.
    """
    if not components or total_lb is None:
        return None
    rows = []
    frac_sum = 0.0
    for comp, w in components.items():
        rows.append({"Component": comp, "Weight %": w, "Pounds (lb)": total_lb * w / 100.0})
        frac_sum += w
    rows.append(
        {
            "Component": "Other / uncharacterized",
            "Weight %": round(100.0 - frac_sum, 4),
            "Pounds (lb)": total_lb * (100.0 - frac_sum) / 100.0,
        }
    )
    rows.append({"Component": "TOTAL", "Weight %": 100.0, "Pounds (lb)": total_lb})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        layout="centered", page_title="Spill Emission Estimator", page_icon=":factory:"
    )

    # Logo + heading
    c1, c2 = st.columns([0.3, 0.7])
    with c1:
        st.image(
            "https://response.restoration.noaa.gov/sites/default/files/skimming_dwh_2010_noaa_520.jpg",
            width=200,
        )
    with c2:
        st.caption("")
        st.header("Spill Emission Estimator")

    if "valid_inputs_received" not in st.session_state:
        st.session_state["valid_inputs_received"] = False

    products, source = load_products()
    product_names = [p["name"] for p in products]

    # ---------------- Sidebar ----------------
    st.sidebar.markdown("**Enter Spill Information Below:**")
    options = product_names + ["Other (manual entry)"]
    select_event = st.sidebar.selectbox("Spilled Material", options)

    selected = next((p for p in products if p["name"] == select_event), None)

    if selected is not None:
        P = st.sidebar.number_input(
            "Material True Vapor Pressure in PSI",
            value=selected["vp_psi"] if selected["vp_psi"] is not None else 0.0,
            step=0.01,
        )
        MW = st.sidebar.number_input(
            "Vapor Molecular Weight",
            value=selected["mw"] if selected["mw"] is not None else 0.0,
            step=0.01,
        )
        if selected["note"]:
            st.sidebar.caption("Profile note: " + selected["note"])
    else:
        P = st.sidebar.number_input("Material True Vapor Pressure in PSI", step=0.01)
        MW = st.sidebar.number_input("Vapor Molecular Weight", step=0.01)
        st.sidebar.caption("Manual product: no speciation profile; only Methods 1 & 2 apply.")

    S = st.sidebar.number_input("Wind Speed in MPH", step=0.1)
    F = st.sidebar.number_input("Material Temperature in Fahrenheit")
    A = st.sidebar.number_input("Spill Surface Area in square feet")
    V = st.sidebar.number_input("Total Spill Volume in Gallons")
    T = st.sidebar.number_input("Total Spill Duration in minutes", value=5)

    with st.sidebar.expander("Product profiles (Google Sheet)"):
        st.caption("Source: " + source)
        st.caption(
            "Products: " + (", ".join(product_names) if product_names else "none")
        )
        st.caption(
            "Add a row to the Google Sheet to add a product — it shows up here "
            "within 10 minutes."
        )
        if st.button("Reload profiles now"):
            load_products.clear()
            st.rerun()
        st.markdown(f"[Open Google Sheet ↗]({SHEET_LINK})")

    # ---------------- Calculation ----------------
    M1 = M2 = M3 = None
    if st.sidebar.button("Calculate", type="primary"):
        if MW is None or MW <= 0:
            st.error("Vapor Molecular Weight must be greater than 0.")
        elif T is None or T <= 0:
            st.error("Spill duration must be greater than 0 (equations use ln(T) / sqrt(T)).")
        else:
            Qr = RMP_equation(mph_mps(S), MW, A, psi_mmhg(P), FtK(F))
            En = EIIPCh16(MW, Ki(MW), A, psi_mmhg(P), FtK(F))
            M1 = Qr * T
            M2 = En * T / 60
            if selected is not None:
                el = empirical_el(selected["name"], F, T)
                M3 = V * el if el is not None else None
            st.session_state["valid_inputs_received"] = True

    st.divider()
    st.subheader("Estimated total emissions")
    mcols = st.columns(3)
    mcols[0].metric("Method 1 · RMP D-1", f"{M1:,.1f} lbs" if M1 is not None else "—")
    mcols[1].metric("Method 2 · EIIP Ch.16", f"{M2:,.1f} lbs" if M2 is not None else "—")
    mcols[2].metric("Method 3 · Empirical", f"{M3:,.1f} lbs" if M3 is not None else "N/A")

    st.subheader("Speciated emissions (component breakdown)")
    if selected is None or not selected["components"]:
        st.info(
            "No speciation profile for this product. Pick a product from the "
            "Google Sheet to see component-level emissions."
        )
    elif M1 is None:
        st.info("Press **Calculate** to see the component breakdown.")
    else:
        st.caption(
            "Component pounds = method total × component weight % from the product "
            "profile. Weight % usually does not sum to 100 — the remainder is "
            "uncharacterized hydrocarbons."
        )
        tabs = st.tabs(["Method 1 · RMP", "Method 2 · EIIP", "Method 3 · Empirical"])
        for tab, total, label in zip(tabs, [M1, M2, M3], ["Method 1", "Method 2", "Method 3"]):
            with tab:
                if total is None:
                    st.write(f"**{label}:** not available for this product.")
                else:
                    df = speciation_rows(total, selected["components"])
                    st.dataframe(
                        df.round({"Weight %": 4, "Pounds (lb)": 2}),
                        hide_index=True,
                        width="stretch",
                    )

    # ---------------- References ----------------
    with st.container(border=1):
        st.markdown(
            """**References:**  
Method 1: [US EPA Risk Management Program Guidance for Offsite Consequence Analysis, Appendix D, Equation D-1](https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf)   
*This method is sensitive to wind speed and assumes a conservative mass transfer coefficient.*

Method 2: [US EPA Emission Inventory Improvement Program, Volume II, Chapter 16, Methods for Estimating Air Emissions from Chemical Manufacturing Facilities, Equation 3-24](https://www.epa.gov/sites/default/files/2015-08/documents/ii16_aug2007final.pdf)    
*Wind speed is not a factor in this method. It can also be used for open top tank emission calculations.*

Method 3: [Merv Fingas: The Evaporation of Oil Spills: Development and Implementation of New Prediction Methodology, Table 7.2](https://www.researchgate.net/publication/272766273_The_Evaporation_of_Oil_Spills_Development_and_Implementation_of_New_Prediction_Methodology)  
*This method uses empirical evaporation equations developed for specific oils by lab experiments. Only products listed in the profile sheet's empirical table have Method 3; new products get Methods 1 & 2 plus speciation.*

Product profiles (vapor pressure, molecular weight, component weight %): [Google Sheet]({SHEET_LINK})"""
        )

    # ---------------- Utility converters ----------------
    with st.container(border=1):
        st.markdown("**Spill volume to surface area conversion**")
        volume = st.number_input("Enter Spill Volume in Gallons")
        depth = st.number_input("Enter Estimated Depth of The Spill in Inches", value=0.5)
        if depth and depth > 0:
            st.write("The Estimated Spill Area is", (volume * 231 / depth) / 144, "Square Feet")
        else:
            st.warning("Depth must be greater than 0.")

    with st.container(border=1):
        st.markdown("**Oil Sheen Area to Volume Conversion**")
        Sheen_Area = st.number_input("Enter Oil Sheen Area in Square Feet")
        st.write(
            "The Estimated Volume of the Spilled Product is",
            (Sheen_Area * (0.0002 / 12)) * 7.481,
            "Gallons",
        )
        st.markdown(
            "*The thickness of oil sheen is assumed to be [0.0002 inch](https://response.restoration.noaa.gov/sites/default/files/OWJA_2016.pdf)*"
        )


if __name__ == "__main__":
    main()
