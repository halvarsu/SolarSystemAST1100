# coding: utf-8
from MySolarSystem import MySolarSystem
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings



import warnings
warnings.filterwarnings("ignore")

class MySateliteSim(MySolarSystem):

    """This is an implementation of My Solar System designed for sending
    satelites into space"""
    au = 149597870700 # m
    year = int(365.25*24*3600) #s

    def __init__(self, seed):
        """TODO: to be defined1.

        :seed: TODO

        """
        MySolarSystem.__init__(self, seed)

        self._seed = seed
        self.planetPos = np.load('positionsHomePlanet.npy')
        self.times = np.load('times.npy')
        self.posFunc  =  self.getPositionsFunction()
        self.velFunc  =  self.getVelocityFunction()
        self.angleFunc =  self.getAngleFunction()
        self.accelFunc = self.getAccelFunction()


    def testVelFunction(self):
        velFunc= self.getVelocityFunction()
        exact = np.linalg.norm((self.vx0[0], self.vy0[0]))
        success = True
        for i in range(10):
            test = np.linalg.norm(velFunc(0, 10**-i), axis = 0)[0]
            print test, abs((test-exact)/exact), "   ", 10**-i
        print exact

    def accelFunction(self, pos, time):
        G = 4*np.pi**2
        mass = self.mass
        r = np.sqrt(pos[0]**2 + pos[1]**2)
        acc = -G*self.starMass*pos/r**3

        planetPositions = self.posFunc(time).T

        for i,posPlanet in enumerate(planetPositions):
            rel_pos = pos - posPlanet
            r2 = rel_pos[0]**2 + rel_pos[1]**2
            acc += -G*mass[i]*rel_pos/(r2*np.sqrt(r2))
        return acc


    def getAccelFunction(self):
        if not hasattr(self, 'accelFunction'):
            self.accelFunction = np.vectorize(self.accelFunc_unvec)
        return self.accelFunction

    def satelite_sim(self, t0 = 0, init_v = 10000, init_angle=1.6*np.pi,
                    tN = 3, dt_far=1/(50000.), dt_close = 1/(365.25*24*3600),
                    sec_per_dt_close= 1, start_dist=1000,
                    start_planet = 0, target_planet = 4, 
                    first_boost = True, pos0=None, vel0=None,
                    sec_per_dt_arrival = 1):
        ''' Init_v in meters per second, t0 in years
        If not first_boost, then pos0 and vel0 will need to be supplied'''
        start = t0
        stop = tN

        dt_close *= sec_per_dt_close
        dt1 = dt_close 
        dt2 =  dt_far
        dt3 = dt_close * sec_per_dt_arrival
        dt = dt1
        print 'DT = ',dt
        dtt = dt*dt

        max_steps = (stop-start)/(dt2) + 1500001
        print max_steps

        if first_boost:
            planetVel0 = self.velFunc(t0)
            planetPos0 = self.posFunc(t0)
            planet_angle = np.arctan(planetPos0[1,start_planet]/planetPos0[0,start_planet])
            if planetPos0[0,start_planet] < 0:
                planet_angle  += np.pi
            theta = init_angle + planet_angle #launch angle

            init_boost = np.array((-init_v*np.sin(theta),
                                    init_v*np.cos(theta)))
            init_dist = start_dist+self.radius[start_planet]
            init_orbit = np.array((init_dist*np.cos(theta),
                                    init_dist*np.sin(theta)))
            pos0 = planetPos0.T[start_planet] + init_orbit/self.au*1000
            vel0 = planetVel0.T[start_planet] + init_boost*self.year/self.au
            

        time_passed = t0

        times = np.zeros((max_steps+1))
        sat_pos = np.zeros((max_steps+1,2))
        sat_vel = np.zeros_like(sat_pos)
        sat_acc = np.zeros_like(sat_pos)
        times[0] = time_passed
        sat_pos[0] = pos0
        sat_vel[0] = vel0
        sat_acc[0] = self.accelFunc(sat_pos[0], time_passed)
        i = 0
        
        new_argmin = 110
        slow = True
        norm = np.linalg.norm
        break_stop = False

        while time_passed <= stop:
            if i >= max_steps or break_stop:
                if not break_stop:
                    print "Encountered max index! Breaking (perhaps) early"
                else:
                    print "Breaking manually"
                break
            sat_pos[i+1] = sat_pos[i] + sat_vel[i]*dt + 0.5*sat_acc[i]*dtt
            sat_acc[i+1] = self.accelFunc(sat_pos[i+1], time_passed)
            sat_vel[i+1] = sat_vel[i] + 0.5*(sat_acc[i] + sat_acc[i+1])*dt

            #sat_vel[i+1] = sat_vel[i] + sat_acc[i]*dt
            #sat_pos[i+1] = sat_pos[i] + sat_vel[i+1]*dt
            #sat_acc[i+1] = self.accelFunc(sat_pos[i+1], time_passed)

            time_passed += dt
            times[i+1] = time_passed
            i+=1
            if i%1000 ==0:

                rel_dist = norm(self.posFunc(time_passed).T-sat_pos[i],axis=1)

                min_value = np.amin(rel_dist)
                min_index = np.argmin(rel_dist)
                acc_now = norm(sat_acc[i])
                print "relative dist to closest(%d): %f  acc: %f  t left: %.3f"\
                        %(min_index,min_value,acc_now, tN-time_passed)

                if min_index == target_planet:
                    if min_value > new_argmin:
                        print 'found minimum', min_value
                        break
                    new_argmin = min_value
                    
                force_relation = norm(sat_pos[i])*np.sqrt(self.starMass*self.mass)

                if slow:
                    '''Sets timestep larger/slower where force from closest
                    planet is as large as force from star
                    '''
                    if np.all(rel_dist[min_index]>force_relation[min_index]/2.):
                        print "i = ", i
                        print "time: ", time_passed
                        dt = dt2
                        dtt = dt*dt
                        print "dt = ", dt
                        slow = False
                        
                else:
                    if np.any(rel_dist[min_index]<force_relation[min_index]/2.): 
                        dt =  dt3
                        dtt = dt*dt
                        print "dt = ", dt
                        slow = True
                        

        # --- end of while loop ---

        self.sat_pos = sat_pos[:i]
        self.sat_vel = sat_vel[:i]
        self.sat_acc = sat_acc[:i]
        self.times = times[:i]

        return sat_pos[:i], sat_vel[:i], sat_acc[:i], times[:i]

    def load_sim(self, fname, folder):
        "fname should be list of pos, vel and times"
        #filenames = 
        self.sat_pos = np.load( folder + fname[0] )
        self.sat_vel = np.load( folder + fname[1] )
        self.times = np.load( folder + fname[2] )

    def plot(self, planet = 5):
        try:
            pos = self.sat_pos
            vel = self.sat_vel
            times = self.times
        except:
            print "simulation must be run before plotting"
            import sys
            sys.exit()

        inner_planets = np.array([0,1,4,5])
        planet_pos = self.posFunc(times)
        planet_vel = self.velFunc(times)

        relpos = pos - planet_pos[:,planet].T
        relvel = vel - planet_vel[:,planet].T
        rel_r = np.linalg.norm(relpos,axis = 1)
        rel_v = np.linalg.norm(relvel,axis = 1)
        closest_i = np.argmin(rel_r)
        print "Closest encounter with %d" %planet, rel_r[closest_i]
        print "Rel speed at CE with %d: " %planet, rel_v[closest_i]

        #relpos *= s.au /1000.
        plt.scatter(0,0,c='y')
        plt.plot(pos[:,0], pos[:,1])
        plt.plot(planet_pos[0,inner_planets].T,
                planet_pos[1,inner_planets].T)
        plt.legend(('satelite', 'planet0'))
        plt.axis('equal')
        plt.show()

        
        theta = np.linspace(0,2*np.pi,20)
        x = self.radius[planet] * np.cos(theta)
        y = self.radius[planet] * np.sin(theta)
        km_relpos = 1./1000 * self.au * relpos
        plt.plot(km_relpos[-5000:,0], km_relpos[-5000:,1])
        plt.scatter(km_relpos[-1,0],km_relpos[-1,1])
        plt.scatter(km_relpos[closest_i,0], km_relpos[closest_i,1])
        plt.plot(x,y)
        plt.axis('equal')
        plt.show()
        
    def saveData(self, fname = ('satPos', 'satVel','satTimes'),
            folder='data'):
        try:
            pos = self.sat_pos
            vel = self.sat_vel
            times = self.times
            data = [pos,vel,times]
        except:
            print "simulation must be run before saving"
            import sys
            sys.exit()

        import glob
        num_old = len(glob.glob('%s/%s*'%(folder,fname[0])))

        for i,name in enumerate(fname):
            full_name = '%s/%s%d' %(folder,name,num_old)
            np.save(full_name, data[i])
            print "Saved file ", full_name


    def orient(self, time):
        planet_pos = self.posFunc(time)
        #rel_pos = 
        
        #for x,y in 
        

# 7.45955363121e-05 collision t14.25, a1.67pi, v9590

if __name__ == "__main__":
    s = MySateliteSim(87464)
    start_time = 14.25 #years
    stop_time = start_time + 3. #years
    init_vel = 9587#m/s
    angle = 1.67*np.pi #radians
    import time
    sim_start = time.time()
    dt_close = 1/(365.25*24*3600)
    for x in range(3):
        pos, vel, acc, times= s.satelite_sim(t0=start_time,
                init_v=init_vel-x,
                tN = stop_time, init_angle = angle, dt_close = dt_close)
        print "length of pos ", pos.shape[0]
        print "Time used on sim: ", time.time() - sim_start,"s"
        norm = np.linalg.norm
        print "Last value: ", norm(pos[-1])
        print "Distance covered: ", norm(pos[0]-pos[-1])
        #s.plot()
        filenames = ['%s%d' %(name,init_vel-x) for name in ('vel','pos','times')]
        s.saveData(filenames)
