def ms_to_auyear(speed):
    au   = 149597871 #km
    year = 3600*24*365.25 #seconds
    return  speed*au*1000/year #m/s to au/year

def test_rocket(num_boxes, boost, dpdt, num_particles_per_sec_one_box,
        calc_fuel):
    from AST1100SolarSystem import AST1100SolarSystem

    au_boost = ms_to_auyear(boost)
    seed = 87464

    system = AST1100SolarSystem(seed)
    system.massNeededCheck(num_boxes, boost, dpdt,
            num_particles_per_sec_one_box, calc_fuel)


if __name__ == "__main__":
    test_rocket()
