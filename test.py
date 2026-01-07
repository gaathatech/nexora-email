import smtplib

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("nexora.aidni@gmail.com", "mqas lqbv khyv dfzm")
print("LOGIN SUCCESS")
server.quit()
