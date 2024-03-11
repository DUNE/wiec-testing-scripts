import os
import csv
import matplotlib
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
from scipy.optimize import curve_fit

class JustPlot:
    def make_plot(self, filename, name, on, pos, ch, fit=None):
        ch1_time, ch1_voltage, ch1_current = self.get_ch_data(os.path.join(self.results_path, f"{filename}.csv"), ch)
        # self.make_plot(f"{self.test_name}_ch0_neg_10k_off", "-2kV to 0, 10k termination", False, False)

        fig = plt.figure(figsize=(16, 12), dpi=80)
        ax = fig.add_subplot(1,1,1)

        ax.plot(ch1_time, ch1_current, label="Ch Current")
        self.format_plot(ax)

        ax2 = ax.twinx()
        ax2.plot(ch1_time, ch1_voltage, label="Ch Voltage", color="red")

        fig.suptitle((name), fontsize=36)

        ax.set_xlabel("Time (Minutes:Seconds)", fontsize=24)
        ax.set_ylabel("Current (uA)", fontsize=24)

        # ax.set_xlim([0,150])
        if (on):
            ax2.set_ylim([15,21])
        elif (not on and not pos):
            ax2.set_ylim([-1,1])
        ax2.set_ylabel("Voltage (V)", fontsize=24)
        self.format_plot(ax2)

        if (on and fit):
            textstr = r'$\tau=%.4f$' % (fit)
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.75, 0.75, textstr, transform=ax.transAxes, fontsize=24,
            verticalalignment='top', bbox=props)

        fig.legend(loc='lower left', prop={'size': 20}, ncol=2)
        ax.yaxis.set_major_formatter('{x:9<5.3f}')
        fig.savefig(os.path.join(self.results_path, f"{filename}.png"))
        plt.close(fig)

    def get_ch_data(self, data_file, ch):
        ch1_datetime = []
        ch1_voltage = []
        ch1_current = []
        with open(data_file, 'r', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            for row in spamreader:
                ch1_datetime.append(datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f'))
                ch1_voltage.append(float(row[1+(ch*2)]))
                ch1_current.append(float(row[2+(ch*2)]))

        first_time = ch1_datetime[0]
        ch1_timedelta = [i-first_time for i in ch1_datetime]
        ch1_time = [datetime(2024, 1, 1, 0, i.seconds//60%60, i.seconds%60, 0) for i in ch1_timedelta]
        return ch1_time, ch1_voltage, ch1_current

    def format_plot(self, ax):
        tick_size = 18
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
        ax.tick_params(axis='x', labelsize=tick_size, colors='black')  # Set tick size and color here
        ax.tick_params(axis='y', labelsize=tick_size, colors='black')  # Set tick size and color here
        ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

if __name__ == "__main__":
    jp = JustPlot()
    jp.results_path = "/home/dune-daq/DUNE-HV-Crate-Testing/results/20240311115712"
    jp.make_plot("20v_hv_ch0_pos_open_on", "0 to 20V, open termination", True, True, 0)
    jp.make_plot("20v_hv_ch0_pos_10k_on", "0 to 20V, 10k termination", True, True, 0)
    jp.make_plot("20v_hv_ch0_neg_open_on", "0 to -20V, open termination", True, False, 8)
    jp.make_plot("20v_hv_ch0_neg_10k_on", "0 to -20V, 10k termination", True, False, 8)
