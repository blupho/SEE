import streamlit as st
############ ETTING UP THE PAGE LAYOUT AND TITLE ############

# `st.set_page_config` is used to display the default layout width, the title of the app, and the emoticon in the browser tab.

st.set_page_config(
    layout="centered", page_title="Spill Emission Estimator", page_icon="❄️"
)

############ CREATE THE LOGO AND HEADING ############

# We create a set of columns to display the logo and the heading next to each other.
# c1, c2 = st.columns([0.32, 2])
# The snowflake logo will be displayed in the first column, on the left.

# with c1:

    # st.image(
#         "images/logo.png",
#         width=85,
#     )


# # The heading will be on the right.

# with c2:
#     st.caption("")
#     st.title("Zero-Shot Text Classifier")


# We need to set up session state via st.session_state so that app interactions don't reset the app.

# if not "valid_inputs_received" in st.session_state:
#     st.session_state["valid_inputs_received"] = False


############ SIDEBAR CONTENT ############

st.sidebar.write("")

# For elements to be displayed in the sidebar, we need to add the sidebar element in the widget.

# We create a text input field for users to enter spill information

S = st.sidebar.number_input("Wind Speed in MPH")
P = st.sidebar.number_input("Vapor Pressure in PSI")
F = st.sidebar.number_input("Temperature in Fahrenheit")
MW = st.sidebar.number_input("Molecular Weight")
A = st.sidebar.number_input("Spill Surface Area in square feet")

# RMP Guidance Equation D-1
#Qr = Evaporation rate (pounds per minute)
# U = Wind speed (meters per second)
# MW = Molecular weight
# A = Surface area of pool formed by the entire quantity of the mixture (square feet)
# VP = Vapor pressure (mm Hg)
# T = Temperature of released substance (Kelvin (K); temperature in C plus 273 or 298 for 25 C)
def RMP_equation(U,MW,A,VP,T):
   Qr = 0.284*(U**0.78)*(MW**(2/3))*A*VP/(82.05*T)
   return Qr
  # print (Qr)
# RMP_equation(10,66,100,5,275)
# mph to m/s conversion
# S = windspeed in mph
def mps_mph(S):
   U = S/2.237
   return U
# psi to mmHg conversion, P = vapor pressure in psi
def mmhg_psi(P):
   VP = 51.751*P
   return VP
# F to K converstion, 
def FtK(F):
   T = (F-32)*5/9+273.15
   return T
#S,P,F,MW,A=int(input("Wind Speed in mph: ")),int(input("Vapor Pressure in psi: ")),int(input("Temperature in F: ")),int(input("Molecular Weight: ")),int(input("Spill Surface Area in square feet: "))
Qr = RMP_equation(mps_mph(S),MW,A,mmhg_psi(P),FtK(F))
st.write("RMP Guidance Equation D-1 Method:",Qr,"lb per minunte")
