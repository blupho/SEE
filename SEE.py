import streamlit as st
import math
# `st.set_page_config` is used to display the default layout width, the title of the app, and the emoticon in the browser tab.

st.set_page_config(
    layout="centered", page_title="Spill Emission Estimator", page_icon=":factory:"
)

#  create 2 columns to display the logo and the heading next to each other.
c1, c2 = st.columns([0.3, 0.7])
# spill boat will be displayed in the first column, on the left.

with c1:
    st.image(
       "https://response.restoration.noaa.gov/sites/default/files/skimming_dwh_2010_noaa_520.jpg",
         width=200,
     )

# # The heading will be on the right.

with c2:
    st.caption("")
    st.header("Spill Emission Estimator")

# set up session state via st.session_state so that app interactions don't reset the app.

if not "valid_inputs_received" in st.session_state:
     st.session_state["valid_inputs_received"] = False


############ SIDEBAR CONTENT ############

st.sidebar.markdown("**Enter Spill Information Below:**")
select_event = st.sidebar.selectbox('Spilled Material',
                                    ['Gasoline', 'WTI Crude','Diesel Fuel','Other'])
S = st.sidebar.number_input("Wind Speed in MPH",step = 0.1)
# P1 = st.empty()
F = st.sidebar.number_input("Material Temperature in Fahrenheit")
# P2 = st.empty()
A = st.sidebar.number_input("Spill Surface Area in square feet")
V = st.sidebar.number_input("Total Spill Volume in Gallons")
T = st.sidebar.number_input("Total Spill Duration in minutes",value=5)
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
# F to C conversion
def FtC(F):
   C = (F-32)*5/9
   return C
# EPA Emission Inventory Improvement Program Chapter 16 Eq. 3-24, Evaporation from an Open Top Vessel or a Spill

def EIIPCh16(Mi,Ki,A,Pisat,Tl):
   En = (Mi*Ki*A*Pisat)/(998.9*Tl)
   return En
def Ki(Mi):
   Ki = 0.83*((18.02/Mi)**(1/3))*118.1102
   return Ki
#Empirical Gasoline Equation
if select_event == 'Gasoline':
 #Default vapor pressure set to 7  
   #with P1.container():
   P = st.sidebar.number_input("Material True Vapor Pressure in PSI",value=7.00,step = 0.01)
 #RVP 7 Gasoline vapor MW according to AP-42 Chapter 7  
   #with P2.container():
   MW = st.sidebar.number_input("Vapor Molecular Weight",value=68.00,step = 0.01)
# Method 3: El is the % of product evaporated after T minutes. Gasoline density 6.07 lb/gal
   El = (13.2+(0.21*FtC(F)))*(math.log(T))*6.07/100
   
#Empirical WTI Crude Equation
if select_event == 'WTI Crude':
 #Default vapor pressure set to 9  
  # with P1.container():
   P = st.sidebar.number_input("Material True Vapor Pressure in PSI",value=9)
 #Crude vapor MW according to AP-42 Chapter 7  
   #with P2.container():
   MW = st.sidebar.number_input("Vapor Molecular Weight",value=50)
# Method 3: El is the % of product evaporated after T minutes. crude density 7.21 lb/gal
   El = (3.08+(0.045*FtC(F)))*(math.log(T))*7.21/100
   
#Empirical Diesel Equation
if select_event == 'Diesel Fuel':
 #Default vapor pressure set to 9  
   #with P1.container():
   P = st.sidebar.number_input("Material True Vapor Pressure in PSI",step=0.001, value=0.006)
 #diesel fuel vapor MW according to AP-42 Chapter 7  
   #with P2.container():
   MW = st.sidebar.number_input("Vapor Molecular Weight",value=130.00,step = 0.01)
# Method 3: El is the % of product evaporated after T minutes. diesel density 7.1 lb/gal
   El = (0.39+(0.013*FtC(F)))*(T**0.5)*7.1/100
   
#Products without Empirical Equations
if select_event == 'Other':
 #Default vapor pressure set to 9  
   #with P1.container():
   P = st.sidebar.number_input("Material True Vapor Pressure in PSI",step = 0.01)
 #diesel fuel vapor MW according to AP-42 Chapter 7  
   #with P2.container():
   MW = st.sidebar.number_input("Vapor Molecular Weight",step = 0.01)
M1 = 0
M2 = 0
M3 = 0
#S,P,F,MW,A=int(input("Wind Speed in mph: ")),int(input("Vapor Pressure in psi: ")),int(input("Temperature in F: ")),int(input("Molecular Weight: ")),int(input("Spill Surface Area in square feet: "))
if st.sidebar.button("Calculate",type="primary"):
   Qr = RMP_equation(mph_mps(S),MW,A,psi_mmhg(P),FtK(F))
   En = EIIPCh16(MW,Ki(MW),A,psi_mmhg(P),FtK(F))
   M1 = Qr*T
   M2 = En*T/60
   if select_event != 'Other':
      M3 = V*El

with st.container(border=1):
   st.write("RMP Guidance Equation D-1 Method:",M1,"pounds")
   st.write("EPA EIIP Chapter 16 Eq. 3-24 Method:",M2,"pounds")
   st.write("Empirical Equation Method:",M3,"pounds")

with st.container(border=1):
   st.markdown('''**References:**  
Method 1: [US EPA Risk Management Program Guidance for Offsite Consequence Analysis, Appendix D, Equation D-1](https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf)   
*This method is sensitive to wind speed and assumes a conservative mass transfer coefficient.*

Method 2: [US EPA Emission Inventory Improvement Program, Volume II, Chapter 16, Methods for Estimating Air Emissions from Chemical Manufacturing Facilities, Equation 3-24](https://www.epa.gov/sites/default/files/2015-08/documents/ii16_aug2007final.pdf)    
*Wind speed is not a factor in this method. It can also be used for open top tank emission calculations.*

Method 3: [Merv Fingas: The Evaporation of Oil Spills: Development and Implementation of New Prediction Methodology, Table 7.2](https://www.researchgate.net/publication/272766273_The_Evaporation_of_Oil_Spills_Development_and_Implementation_of_New_Prediction_Methodology)  
*This method uses empirical evaporation equations developed for specific oils by lab experiments, spill volume, time and temperature are the only factors*''')

with st.container(border=1):
   st.markdown("**Spill volume to surface area conversion**")
   volume = st.number_input("Enter Spill Volume in Gallons")
   depth = st.number_input("Enter Estimated Depth of The Spill in Inches", value=0.5)
   st.write("The Estimated Spill Area is",(volume*231/depth)/144,"Square Feet")

with st.container(border=1):
   st.markdown("**Oil Sheen Area to Volume Conversion**")
   Sheen_Area = st.number_input("Enter Oil Sheen Area in Square Feet")
   st.write("The Estimated Volume of the Spilled Product is",(Sheen_Area*(0.0002/12))*7.481,"Gallons")
   st.markdown("*The thickness of oil sheen is assumed to be [0.0002 inch](https://response.restoration.noaa.gov/sites/default/files/OWJA_2016.pdf)*")
