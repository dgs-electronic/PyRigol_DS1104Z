import visa
import matplotlib
from math import ceil
import matplotlib.pyplot as pl
import scipy.signal.windows as win
from numpy import abs, log10
from numpy.fft import fftshift, fftfreq
from scipy.fftpack import fft, next_fast_len
from matplotlib.pyplot import plot, semilogx, grid, loglog, semilogy, figure, xlabel, ylabel, legend, show


matplotlib.use('TkAgg')

class Trace:
    def __init__(self,instrument):
        self.time = []
        self.volt = []
        self.freq = []
        self.spectrum = []
        self.samplingrate = 0
        self.dso = instrument
        self.timedivision = 0
        self.voltagedivision = 0
        self.offset = 0

    def getIdentity(self):
        return self.dso.query("*IDN?")

    def autoScale(self):
        self.dso.write(":AUT")
        return "-DONE-"

    def clearAll(self):
        self.dso.write(":CLE")
        return "-DONE-"

    def run(self):
        self.dso.write(":RUN")
        return "-DONE-"

    def stop(self):
        self.dso.write(":STOP")
        return "-DONE-"

    def singleshot(self):
        self.dso.write(":SING")
        return "-DONE-"

    def forceTrigger(self):
        self.dso.write(":TFOR")
        return "-DONE-"

    def setAveraging(self,count):
        self.dso.write(":ACQ:AVER "+str(count))
        return self.dso.query(":ACQ:AVER?")

    def setMemoryDepth(self,count):
        self.dso.write(":ACQ:MDEP "+str(count))
        return self.dso.query(":ACQ:MDEP?")

    def setAcquire(self,mode="NORM"):        #mode NORM,AVER,PEAK,HRES
        self.dso.write(":ACQ:TYP "+mode)
        return self.dso.query(":ACQ:TYP?")

    def getSamplingRate(self):
        return float(self.dso.query(":ACQ:SRAT?"))

    def getVoltageOffset(self,channel):
        return float(self.dso.query(":CHAN"+str(channel)+":OFFS?"))

    def getVoltageDivision(self,channel):
        return float(self.dso.query(":CHAN"+str(channel)+":SCAL?"))

    def getTimeDivision(self):
        return float(self.dso.query(":TIM:MAIN:SCAL?"))




    def getTrace(self,channel):
        self.dso.timeout = 60000
        self.dso.chunk_size = 250000

        maxbytes_per_read = 250000
        self.stop()
        samplecnt = float(self.dso.query(":ACQ:MDEP?"))
        print("Anzahl der Samples: "+str(samplecnt))

        self.dso.write(":WAV:SOUR CHAN" + str(channel))
        self.dso.write(":WAV:MODE RAW")

        self.dso.write(":WAV:FORM BYTE")
        self.dso.write(":WAV:STAR 1")
        self.dso.write(":WAV:STOP 250000")

        #X-Achsen Parameter holen
        tinc = float(self.dso.query(":WAV:XINC?"))    #Time increment per sample
        print("Timestep = "+str(tinc)+" sec")
        torigin = float(self.dso.query(":WAV:XOR?")) #Time origin
        print("Time-Origin = "+str(torigin)+" sec")
        tref = float(self.dso.query(":WAV:XREF?")) #Time Reference
        print("Time Reference = "+str(tref)+" sec")

        #Y-Achsen Parameter holen
        vinc = float(self.dso.query(":WAV:YINC?")) #Voltage Inkrement
        print("Voltagestep = "+str(vinc)+" V")
        vorigin = float(self.dso.query(":WAV:YOR?"))
        print("Voltage Origin = "+str(vorigin)+" steps")
        vref = float(self.dso.query(":WAV:YREF?"))
        print("Voltage Ref = "+str(vref)+ " steps")


        vdiv = self.getVoltageDivision(channel)
        ofst = self.getVoltageOffset(channel)
        tdiv = self.getTimeDivision()
        sara = self.getSamplingRate()



        #Rohwerte holen
        raw_value = []
        chunk_cnt = ceil(samplecnt/maxbytes_per_read)
        print("Anzahl der Chunks: "+str(chunk_cnt))
        for cnt in range(0,chunk_cnt):
            self.dso.write(":WAV:STAR "+str(cnt*maxbytes_per_read+1))
            self.dso.write(":WAV:STOP "+str((cnt+1)*maxbytes_per_read))
            self.dso.write(":WAV:DATA?")
            recv = list(self.dso.read_raw())[12:]
            recv.pop()
            raw_value = raw_value + recv #Listen zusammenhängen
            print("Chunk " + str(cnt) + " Von: "+str(cnt*maxbytes_per_read+1)+" bis "+ str((cnt+1)*maxbytes_per_read))

        #Spannungs Rohwerte umrechnen
        volt_value = []
        for data in raw_value:
            data = vinc*(data-vref-vorigin)
            volt_value.append(data)

        #Zeit Rohwerte umrechnen
        time_value = []
        for idx in range(0, len(volt_value)):
            time_data = torigin + idx * tinc
            time_value.append(time_data)

        # Werte in Objekt-Variablen überspielen
        self.voltagedivision = vdiv
        self.timedivision = tdiv
        self.samplingrate = sara
        self.offset = ofst
        self.time = time_value
        self.volt = volt_value
        self.run()
        return '-DONE-'


    def plotTrace(self, titel="Trace1"):
        figure(figsize=(7, 5))
        plot(self.time, self.volt, 'r', markersize=1, label=titel)
        xlabel("Frequency [s]")
        ylabel("Amplitude [V]")
        legend()
        grid(b=True, which='major', color='g', linestyle='-')
        grid(b=True, which='minor', color='g', linestyle='-')
        show()
        return '-DONE-'


#main
_rm = visa.ResourceManager()
sds = _rm.open_resource("TCPIP::192.168.178.69::INSTR")

rigol = Trace(sds)

print(rigol.getIdentity())
#print(rigol.autoScale())
#print("Samplingrate:")
#print(rigol.getSamplingRate())
#print("TimeDivision:")
#print(rigol.getTimeDivision())
#print("Voltage-Division:")
#print(rigol.getVoltageDivision(1))
#print("Voltage-Offset:")
#print(rigol.getVoltageOffset(1))
rigol.getTrace(1)

print(len(rigol.volt))

rigol.plotTrace()

sds.close()