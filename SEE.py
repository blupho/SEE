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
S,P,F,MW,A=int(input("Wind Speed in mph: ")),int(input("Vapor Pressure in psi: ")),int(input("Temperature in F: ")),int(input("Molecular Weight: ")),int(input("Spill Surface Area in square feet: "))
print (RMP_equation(mps_mph(S),MW,A,mmhg_psi(P),FtK(F)))

