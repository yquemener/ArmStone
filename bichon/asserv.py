from pyvesc import VESC

class SpeedController :
    def __init__ (self, vescpath) :
        self.rpmobj = 0
        self.k = 0.001
        self.rpml = list()
        self.vesc = VESC(serial_port=vescpath)
        self.current_duty_cycle = 0

    def set_duty_cycle(self, val):
        if val>0.5:
            val=0.5
        if val<-0.5:
            val=-0.5
        self.vesc.set_duty_cycle(val)
    
    def asserv(self, rpm):
        err = self.rpmobj - rpm
        delta = self.k * err
        return(delta)
    
    def cycle(self):

        try:
            rpm = -self.vesc.get_rpm()
        except AttributeError:
            return

        self.current_duty_cycle = self.current_duty_cycle+self.asserv(rpm)  
        self.set_duty_cycle(self.current_duty_cycle)