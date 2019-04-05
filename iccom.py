import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.widgets import Slider

import numpy as np
import ngspicepy as ng
import sys

output_csv = ["1_1_output23_10_18.csv", "2_3_output23_10_18.csv", "3_1_output23_10_18.csv"]
vd_csv = ["1_1_vs1_23_10_18.csv", "2_3_vd1_23_10_18.csv", "3_1_vd1_23_10_18.csv"]
odset = 0
vdset = 2

thickness = [(5,"5nm_vd=1_23_10_18.csv"), (8,"8nm_vd=1_23_10_18.csv"), (10,"10nm_vd=1_23_10_18.csv"), (25,"25nm_vd=1_23_10_18.csv")]

#simData = pd.read_csv("jv.dat", header=None, names=["v","j"], sep=" ", comment="#")


NETLIST = """
.title IGZO TFT


*X1 N002 N001 0 igzotft
M1 N001 N002 0 0 IGZO_NMOS L=60u W=2m
*x1  N002 N001 0 igzotft
VG N002 0 1
VD N001 0 1


.subckt igzotft n1 n2 n3
M1 n2 n1 n3 3 IGZO_NMOS L=60u W=2m
.ends


.model IGZO_NMOS NMOS
%s


.options savecurrents
*.dc VD -0.2 1 0.1 VG 0.5 1 0.1


.end
"""

#Level 1
defaultParamsMos1 = {
                 "is": (1.48e-10, (-15,-9),True),
                 "rd":  (82, (0, 2000), False),
                 "rs":  (180, (0, 2000), False),
                 "cox": (3.45e-4, (-5, -1), True),
                 "kp": (6.61e-6, (-5.6,-5),True),
                 "gamma":  (0, (0, 2), False),
                 "phi":  (0.6, (0, 4), False),
                 "lambda": (0.03, (0, 0.1), False),
                 "pb":  (0.8, (0, 2), False),
                 "ld":  (0, (0, 10), False),
                 "tox": (1e-7, (-9, 5), True),
                 "vto": (0.36, (0.2, 0.4), False),
                 "uo":  (10, (1, 1000), False)}


defaultParamsMos3 = {
                 "is":  (1.48e-10, (-14, -4), True),
                 "vto": (0.34, (0.2, 0.5), False),
                 "rd":  (169, (0, 3000), False),
                 "rs":  (855, (0, 3000), False),
                 "kp":  (6.76e-6, (-7, -2), True),
                 "gamma":  (3.27e-5, (-9, -2), True),
                 "phi":  (0.6, (0, 5), False),
                 "pb":  (0.8, (0, 1), False),
                 "ld":  (0, (0, 1), False),
                 #"cj":  (0, (0, 1), False),
                 #"mj":  (0.5, (0, 1), False),
                # "js":  (0, (0, 1), False),
                 "nsub":  (1.62e13, (13, 19), True),
                 "tox":  (1e-7, (-10, -6), True),
                 "nss":  (0.25, (0, 1), False),
                 "vmax":  (338, (-6, 8), True),
                 "xj":  (0.186, (-2, 1), True),
                 "nfs":  (1.7e11, (8, 12), True),
                 "kappa":  (0.2, (0, 1), False),
                 "theta":  (0, (0, 1), False),
                 "delta":  (0, (0, 1), False),
                 "uo":  (10.7, (1, 100), False)}

# defaultParams = {"is":  (1.48e-10, (-11, -9), True),
#                  "vto": (0.34, (0.3, 0.4), False),
#                  "rd":  (0, (0, 3000), False),
#                  "rs":  (0, (0, 3000), False),
#                  "kp":  (6.61e-6, (-7, -2), True),
#                  "gamma":  (0, (0, 3), False),
#                  "phi":  (0.6, (0, 5), False),
#                  "pb":  (0.8, (0, 1), False),
#                  "ld":  (0, (0, 1000), False),
#                  "rsh":  (0, (0, 1), False),
#                  "nsub":  (1.62e13, (0, 19), True),
#                  "xj":  (0, (0, 100), False),
                 
#                  "nfs":  (0.8, (0, 1), False),
#                  "tox":  (1e-7, (-10, -6), True),
#                  "nss":  (0, (0, 1), False),
#                  "vmax":  (1.1e-5, (-6, 8), True),
#                  #"xj":  (1e-2, (-2, 1), True),
#                  "uo":  (10, (1, 1000), False)}








# defaultParams = {"vfb":  (1.66e-10, (-14, -4), True),
#                  "phi": (0.34, (0.2, 0.5), False),
#                  "k1":  (169, (0, 3000), False),
#                  "k2":  (855, (0, 3000), False),
#                  "eta":  (6.76e-6, (-7, -2), True),
#                  "muz":  (3.27e-5, (-9, -2), True),
#                  "dl":  (0.0589, (-5, 5), True),
#                  "dw":  (0, (0, 0.01), False),
#                  "u0":  (0, (0, 0.01), False),
#                  "u1":  (0.8, (0, 1), False)}

class Parameter():
    def __init__(self, name, value, range, log, ax):
        self.name = name
        self.value = value
        self.range = range
        self.log = log

        if(log):
            valInit = np.log10(value)
        else:
            valInit = value

        self.slider = Slider(ax, name, range[0], range[1], valinit=valInit, valstep=0.01)

    def updateVal(self):
        if(self.log):
            newVal = 10**(self.slider.val)
            self.slider.valtext.set_text("%.3g" % newVal)
        else:
            newVal = self.slider.val

        self.value = newVal


class Model():
    def __init__(self, level, defaultParams, netlist):
        self.tftModel = {}
        self.netlist = netlist
        self.level = level
        self.figC = plt.figure("Controlls")
        Nparam = len(defaultParams)
        for i, (k, v) in enumerate(defaultParams.items()):
            axSlider = plt.axes([0.1,0.045*(Nparam - (i)),0.8,0.04]) #([0.1, 0.1, 0.75, 0.03])

            self.tftModel[k] = Parameter(k, v[0], v[1], v[2], axSlider)


    def getNetlist(self):
        modelString = "+level=%s\n"%str(self.level)
        for k, v in self.tftModel.items():
            modelString += "+%s=%g\n" % (k, v.value)
        return self.netlist % modelString



    def simulate(self):
        ng.reset()
        netlist = self.getNetlist()
        print(netlist)

        ng.load_netlist(netlist)
        ng.run_dc('vd -0 1 0.01 vg 0.5 1 0.1')

        vecs_data = ng.get_all_data()

        vd = vecs_data['n001'].reshape((6, 101))
        vg = vecs_data['n002'].reshape((6, 101))
        ids = vecs_data['@m1[id]'].reshape((6, 101))
        igs = vecs_data['@m1[ig]'].reshape((6, 101))

        return (vd.copy(), vg.copy(), ids.copy(), igs.copy())

    def simulateIDVG(self):
        ng.reset()
        netlist = self.getNetlist()
        #print(netlist)
        ng.load_netlist(netlist)
        ng.run_dc('vg -0.5 1 0.01')
        vecs_data = ng.get_all_data()


        vg = vecs_data['n002']
        ids = vecs_data['@m1[id]']
        igs = vecs_data['@m1[ig]']

        return (vg.copy(), ids.copy(), igs.copy())

    def update(self):
        for k, v in self.tftModel.items():
            v.updateVal()

    def setUpdate(self, function):
        for k, v in self.tftModel.items():
            v.slider.on_changed(function)




#m = Model(1, defaultParamsMos1, NETLIST)
m = Model(3, defaultParamsMos3, NETLIST)


sim_vd, sim_vg, sim_ids, sim_igs = m.simulate()


data = pd.read_csv('data/'+output_csv[odset]).groupby("VG")

figIDVD, (axIDVD,axIDVG) = plt.subplots(1, 2, tight_layout=True)
axIDVD.set_title(r"$I_D V_D$ Plot - Output")
# plt.subplots_adjust(bottom=0.25)
axIDVD.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
sim_lines = []
mes_lines = []
for j, (vg, d) in enumerate(data):
    #mes_lines.append(plt.plot(d["VD"], d["ID"], label="vg:%s" % vg))
    mes_lines.append(axIDVD.plot(d["VD"], d["ID"], label=r"$V_G$:%s" % vg))
    sim_lines.append(axIDVD.plot(sim_vd[j], sim_ids[j], '--', color=mes_lines[-1][0].get_color(), label=r"$V_G$:%s Sim" % vg))
axIDVD.legend()
axIDVD.grid()
axIDVD.set_xlabel(r"$V_D$ [V]")
axIDVD.set_ylabel(r"$I_D$ [A]")
axIDVD.autoscale(axis='y')



sim_vg_vg, sim_ids_vg, sim_igs_vg = m.simulateIDVG()



axIDVG.set_title(r"$I_D V_G$ Plot - Transfer")
# plt.subplots_adjust(bottom=0.25)
axIDVG.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
sim_linesIDVG = []
mes_linesIDVG = []

d = pd.read_csv('data/'+vd_csv[vdset])
mes_linesIDVG.append(axIDVG.semilogy(d["VG"], d["ID"], label=r"$I_D$"))
sim_linesIDVG.append(axIDVG.semilogy(sim_vg_vg, sim_ids_vg, '--', color=mes_linesIDVG[-1][0].get_color(), label=r"$I_D$ Sim"))
mes_linesIDVG.append(axIDVG.semilogy(d["VG"], np.abs(d["IG"]), label=r"$I_G$"))
sim_linesIDVG.append(axIDVG.semilogy(sim_vg_vg, np.abs(sim_igs_vg), '--', color=mes_linesIDVG[-1][0].get_color(), label=r"$I_G$ Sim"))

axIDVG.set_xlabel(r"$V_G$ [V]")
axIDVG.set_ylabel(r"$I_D$ [A]")
axIDVG.legend()
axIDVG.grid()



# for j, (vg, d) in enumerate(data):
#     mes_lines.append(plt.plot(d["VD"], d["ID"], label="vg:%s" % vg))
#     sim_lines.append(plt.plot(sim_vd[j], sim_ids[j], '--', color=mes_lines[-1][0].get_color(), label="simvg:%s" % vg))
# plt.legend()
# plt.xlabel("VD [V]")
# plt.ylabel("ID [A]")
# plt.autoscale(axis='y')









figT, ax = plt.subplots(1,1)
sim_t = []
for t,tf in thickness:
    vg, ids, igs = m.simulateIDVG()
    data = pd.read_csv('thickness/'+tf)
    filter1 = data["mes"]== 2
    filter2 = data["scanDir"] == 1
    data.where(filter1 & filter2, inplace=True)
    color = next(ax._get_lines.prop_cycler)['color']
    ax.semilogy(data['vg'], data['id'], color=color, label=r"$I_D$ " + str(t) + "nm" )
    ax.semilogy(data['vg'], np.abs(data['ig']), "--", color=color, label=r"$I_G$ " + str(t) + "nm" )
    sim_t.append(ax.semilogy(vg, np.abs(ids), ".", color=color, label=str(t) + "nm" ))

ax.set_xlabel(r"$V_G$ [V]")
ax.set_ylabel(r"$I_D$ [A]")
ax.grid()
ax.legend()





def update(val):
    m.update()

    sim_vg_vg, sim_ids_vg, sim_igs_vg = m.simulateIDVG()
    sim_vd, sim_vg, sim_ids, sim_igs = m.simulate()

    for i, line in enumerate(sim_lines):
        line[0].set_ydata(sim_ids[i])
  

    sim_linesIDVG[0][0].set_ydata(sim_ids_vg)

    for i, (t, tf) in enumerate(thickness):
        sim_vg_vg, sim_ids_vg, sim_igs_vg = m.simulateIDVG()
        sim_t[i][0].set_ydata(sim_ids_vg)

    figIDVD.canvas.draw_idle()
    figT.canvas.draw_idle()




update(0)
m.setUpdate(update)






plt.show()



