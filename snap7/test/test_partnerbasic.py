import snap7

passive = snap7.partner.Partner(active=False)
active = snap7.partner.Partner(active=True)
passive.start_to("0.0.0.0", "127.0.0.1", 1002, 1000)
active.start_to("0.0.0.0", "127.0.0.1", 1000, 1002)
print active.get_status().value
#1 # (Running, active and trying to connect.)
print passive.get_status().value

