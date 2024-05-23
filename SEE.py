import streamlit as st

# `st.set_page_config` is used to display the default layout width, the title of the app, and the emoticon in the browser tab.

st.set_page_config(
    layout="centered", page_title="Spill Emission Estimator", page_icon=":factory:"
)

#  create 2 columns to display the logo and the heading next to each other.
c1, c2 = st.columns([2, 6])
# spill boat will be displayed in the first column, on the left.

with c1:
    st.image(
       "https://response.restoration.noaa.gov/sites/default/files/skimming_dwh_2010_noaa_520.jpg",
         width=180,
     )

# # The heading will be on the right.

with c2:
    st.caption("")
    st.title("Spill Emission Estimator")

# set up session state via st.session_state so that app interactions don't reset the app.

if not "valid_inputs_received" in st.session_state:
     st.session_state["valid_inputs_received"] = False


############ SIDEBAR CONTENT ############

st.sidebar.write("**Spill Information:**")
S = st.sidebar.number_input("Wind Speed in MPH",step = 0.1)
P = st.sidebar.number_input("Material True Vapor Pressure in PSI")
F = st.sidebar.number_input("Material Temperature in Fahrenheit")
MW = st.sidebar.number_input("Vapor Molecular Weight",value=68 )
A = st.sidebar.number_input("Spill Surface Area in square feet")
T = st.sidebar.number_input("Total Spill Duration in minutes")
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
def mph_mps(S):
   U = S/2.237
   return U
# psi to mmHg conversion, P = vapor pressure in psi
def psi_mmhg(P):
   VP = 51.751*P
   return VP
# F to K converstion, 
def FtK(F):
   T = (F-32)*5/9+273.15
   return T
# EPA Emission Inventory Improvement Program Chapter 16 Eq. 3-24, Evaporation from an Open Top Vessel or a Spill
def EIIPCh16(Mi,Ki,A,Pisat,Tl):
   En = (Mi*Ki*A*Pisat)/(998.9*Tl)
   return En
def Ki(Mi):
   Ki = 0.83*((18.02/Mi)**(1/3))*118.1102
   return Ki
#S,P,F,MW,A=int(input("Wind Speed in mph: ")),int(input("Vapor Pressure in psi: ")),int(input("Temperature in F: ")),int(input("Molecular Weight: ")),int(input("Spill Surface Area in square feet: "))
Qr = RMP_equation(mph_mps(S),MW,A,psi_mmhg(P),FtK(F))
En = EIIPCh16(MW,Ki(MW),A,psi_mmhg(P),FtK(F))
if st.sidebar.button("Calculate",type="primary"):
    st.write("RMP Guidance Equation D-1 Method:",Qr*T,"pounds")
    st.write("EPA EIIP Chapter 16 Eq. 3-24 Method:",En*T/60,"pounds")
st.success('''**References:**  
Method 1: [US EPA Risk Management Program Guidance for Offsite Consequence Analysis, Appendix D, Equation D-1](https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf)   
*This method is sensitive to wind speed and assumes a conservative mass transfer coefficient.*

Method 2: [US EPA Emission Inventory Improvement Program, Volume II, Chapter 16, Methods for Estimating Air Emissions from Chemical Manufacturing Facilities, Equation 3-24](https://www.epa.gov/sites/default/files/2015-08/documents/ii16_aug2007final.pdf)    
*Wind speed is not a factor in this method. It can also be used for open top tank emission calculations.*

Method 3: [Merv Fingas: The Evaporation of Oil Spills: Development and Implementation of New Prediction Methodology, Table 7.2](https://www.researchgate.net/publication/272766273_The_Evaporation_of_Oil_Spills_Development_and_Implementation_of_New_Prediction_Methodology)
*This method uses empirical evaporation equations developed for specifice oils by lab experiments, time and temperature are the only factors*''')
