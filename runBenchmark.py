# script to run the simulation in the shell, in a loop, with different parameters
# and parse the shell putput for certain lines to extract the performance metrics
# and plot them in a graph

import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np

# parameters
numRuns = 1
benchmark_lengths = [100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
# benchmark_lengths = [100, 1000, 10000, 100000, 1000000]
# run the simulation in a loop
results_no_perf = []
results_og_tracegen = []
results_new_tracegen = []

# run simulation for no performance model
print("Running no performance model")
for length in benchmark_lengths:
    print("Running benchmark with length " + str(length))
    for i in range(numRuns):
        print("Run " + str(i))
        # run the benchmark by running './scripts/run.sh dhry:{length} cv32e40p -np' in the shell
        result = subprocess.run(['./scripts/run.sh', 'dhry:' + str(length), 'cv32e40p', '-np'], stdout=subprocess.PIPE)
        # parse the shell output for the performance metrics
        # extract the execution time of the benchmark from the line "Total execution time: {exe_time}s" out of all lines in the output
        exe_time_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Total execution time" in line][0]
        exe_time = float(exe_time_line.split(": ")[1].split("s")[0])
        print("execution time = " + str(exe_time) + "s")
        # extract the MIPS value of the benchmark from the line "MIPS (estimated): {mips}" out of all lines in the output
        mips_line = [line for line in result.stdout.decode('utf-8').split('\n') if "MIPS (estimated)" in line][0]
        mips = float(mips_line.split(": ")[1])
        print("MIPS = " + str(mips))
        # add the performance metrics to the results list
        results_no_perf.append({"length": length, "run": i, "exe_time": exe_time, "mips": mips})

# run simulation for new tracegen
print("Running new tracegen")
for length in benchmark_lengths:
    print("Running benchmark with length " + str(length))
    for i in range(numRuns):
        print("Run " + str(i))
        # run the benchmark by running './scripts/run.sh dhry:{length} cv32e40p' in the shell
        result = subprocess.run(['./scripts/run.sh', 'dhry:' + str(length), 'cv32e40p'], stdout=subprocess.PIPE)
        # parse the shell output for the performance metrics
        # extract the number of instructions from the line ">> Number of instructions: {num_instr}" out of all lines in the output
        instr_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Number of instructions" in line][0]
        num_instr = int(instr_line.split(": ")[1])
        # extract the CPI of the processor from the line "Estimated average number of processor cycles per instruction: {CPI}" out of all lines in the output
        cpi_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Estimated average number of processor cycles per instruction" in line][0]
        cpi = float(cpi_line.split(": ")[1])
        # extract the execution time of the benchmark from the line "Total execution time: {exe_time}s" out of all lines in the output
        exe_time_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Total execution time" in line][0]
        exe_time = float(exe_time_line.split(": ")[1].split("s")[0])
        print("execution time = " + str(exe_time) + "s")
        # calculate the MIPS by dividing the number of instructions by the execution time
        mips = num_instr / (exe_time * 1000000)
        print("MIPS = " + str(mips))
        # add the performance metrics to the results list
        results_new_tracegen.append({"length": length, "run": i, "num_instr": num_instr, "cpi": cpi, "exe_time": exe_time, "mips": mips})

# go up a directory and change the directory to the Perf_sim_test directory
os.chdir("../Perf_sim_test")

# run the simulation for the original tracegen
print("Running original tracegen")
for length in benchmark_lengths:
    print("Running benchmark with length " + str(length))
    for i in range(numRuns):
        print("Run " + str(i))
        # run the benchmark by running './scripts/run.sh dhry:{length} cv32e40p' in the shell
        result = subprocess.run(['./scripts/run.sh', 'dhry:' + str(length), 'cv32e40p'], stdout=subprocess.PIPE)
        # parse the shell output for the performance metrics
        # extract the number of instructions from the line ">> Number of instructions: {num_instr}" out of all lines in the output
        instr_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Number of instructions" in line][0]
        num_instr = int(instr_line.split(": ")[1])
        # extract the CPI of the processor from the line "Estimated average number of processor cycles per instruction: {CPI}" out of all lines in the output
        cpi_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Estimated average number of processor cycles per instruction" in line][0]
        cpi = float(cpi_line.split(": ")[1])
        # extract the execution time of the benchmark from the line "Total execution time: {exe_time}s" out of all lines in the output
        exe_time_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Total execution time" in line][0]
        exe_time = float(exe_time_line.split(": ")[1].split("s")[0])
        print("execution time = " + str(exe_time) + "s")
        # calculate the MIPS by dividing the number of instructions by the execution time
        mips = num_instr / (exe_time * 1000000)
        print("MIPS = " + str(mips))
        # add the performance metrics to the results list
        results_og_tracegen.append({"length": length, "run": i, "num_instr": num_instr, "cpi": cpi, "exe_time": exe_time, "mips": mips})

os.chdir("../PerformanceSimulation_workspace")

# save the results to a file
with open("results_no_perf_no_res_cv32e40p.txt", "w") as file:
    for result in results_no_perf:
        file.write(str(result) + "\n")

with open("results_og_tracegen_no_res_cv32e40p.txt", "w") as file:
    for result in results_og_tracegen:
        file.write(str(result) + "\n")

with open("results_new_tracegen_no_res_cv32e40p.txt", "w") as file:
    for result in results_new_tracegen:
        file.write(str(result) + "\n")

# plot the results
fig, axs = plt.subplots(1, 2, figsize=(12, 6))
fig.suptitle('Performance metrics of the benchmark')

# Plot Execution time (no perf in red, og tracegen in blue, new tracegen in green)
axs[0].plot([result["length"] for result in results_no_perf], [result["exe_time"] for result in results_no_perf], 'r')
axs[0].plot([result["length"] for result in results_og_tracegen], [result["exe_time"] for result in results_og_tracegen], 'b')
axs[0].plot([result["length"] for result in results_new_tracegen], [result["exe_time"] for result in results_new_tracegen], 'g')
axs[0].set_title('Execution time')
axs[0].set_xscale('log')
axs[0].set_yscale('log')
axs[0].set_xlabel('Benchmark length')
axs[0].set_ylabel('Execution time (s)')
#set grid on
axs[0].grid()
# show legend
axs[0].legend(['No perf', 'Original tracegen', 'New tracegen'])

# Plot MIPS (no perf in red, og tracegen in blue, new tracegen in green)
# make a horizontal line for the max MIPS value of the no performance model
final_mips_no_perf = max([result["mips"] for result in results_no_perf])
axs[1].axhline(y=final_mips_no_perf, color='r', linestyle='--')
axs[1].plot([result["length"] for result in results_no_perf], [result["mips"] for result in results_no_perf], 'r')
# make a horizontal line for the max MIPS value of the original tracegen
final_mips_og_tracegen = max([result["mips"] for result in results_og_tracegen])
axs[1].axhline(y=final_mips_og_tracegen, color='b', linestyle='--')
axs[1].plot([result["length"] for result in results_og_tracegen], [result["mips"] for result in results_og_tracegen], 'b')
# make a horizontal line for the max MIPS value of the new tracegen
final_mips_new_tracegen = max([result["mips"] for result in results_new_tracegen])
axs[1].axhline(y=final_mips_new_tracegen, color='g', linestyle='--')
axs[1].plot([result["length"] for result in results_new_tracegen], [result["mips"] for result in results_new_tracegen], 'g')
axs[1].set_title('MIPS')
axs[1].set_xscale('log')
# set y axis to linear scale
axs[1].set_yscale('linear')
axs[1].set_xlabel('Benchmark length')
axs[1].set_ylabel('MIPS')
axs[1].grid()
axs[1].legend(['No perf Max', 'No perf', 'Original tracegen Max', 'Original tracegen', 'New tracegen with $resolved Max', 'New tracegen with $resolved'])

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# save the plot to a file
fig.savefig("Results_no_resolved_cv32e40p.png")

        