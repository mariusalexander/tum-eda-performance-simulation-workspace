# script to run the simulation in the shell, in a loop, with different parameters
# and parse the shell putput for certain lines to extract the performance metrics
# and plot them in a graph

import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np

# parameters
numRuns = 5
benchmark_lengths = [100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
# benchmark_lengths = [100, 1000, 10000, 100000, 1000000]
# run the simulation in a loop
results_no_perf = []
results_og_tracegen = []
results_new_tracegen = []

# go up a directory and change the directory to the Perf_sim_test directory
os.chdir("../Perf_sim_test")

# run the simulation for the original tracegen
print("Running original tracegen")
# print current working directory
print(os.getcwd())
for length in benchmark_lengths:
    print("Running benchmark with length " + str(length))
    for i in range(numRuns):
        print("Run " + str(i))
        # run the benchmark by running './scripts/run.sh dhry:{length} cv32e40p in the shell
        result = subprocess.run(['./scripts/run.sh', 'dhry:' + str(length), 'cv32e40p'], stdout=subprocess.PIPE)
        # parse the shell output for the performance metrics
        # extract the execution time of the benchmark from the line "Total execution time: {exe_time}s" out of all lines in the output
        exe_time_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Total execution time" in line][0]
        exe_time = float(exe_time_line.split(": ")[1].split("s")[0])
        print("execution time = " + str(exe_time) + "s")
        # extract the MIPS value of the benchmark from the line "MIPS (estimated): {mips}" out of all lines in the output
        mips_line = [line for line in result.stdout.decode('utf-8').split('\n') if "MIPS (estimated)" in line][0]
        mips = float(mips_line.split(": ")[1])
        print("MIPS = " + str(mips))
        # extract the num_instr value of the benchmark from the line "CPU Cycles (estimated): {num_instr}" out of all lines in the output
        num_instr_line = [line for line in result.stdout.decode('utf-8').split('\n') if "CPU Cycles (estimated)" in line][0]
        num_instr = float(num_instr_line.split(": ")[1])
        # add the performance metrics to the results list
        results_og_tracegen.append({"length": length, "run": i, "num_instr": num_instr, "exe_time": exe_time, "mips": mips})
    # average the results for the same benchmark length
    avg_num_instr = np.mean([result["num_instr"] for result in results_og_tracegen if result["length"] == length])
    avg_exe_time = np.mean([result["exe_time"] for result in results_og_tracegen if result["length"] == length])
    avg_mips = np.mean([result["mips"] for result in results_og_tracegen if result["length"] == length])
    results_og_tracegen.append({"length": length, "run": "avg", "num_instr": avg_num_instr, "exe_time": avg_exe_time, "mips": avg_mips})

os.chdir("../PerformanceSimulation_workspace")

# run simulation for no performance model
print("Running new tracegen")
# print current working directory
print(os.getcwd())
for length in benchmark_lengths:
    print("Running benchmark with length " + str(length))
    for i in range(numRuns):
        print("Run " + str(i))
        # run the benchmark by running './scripts/run.sh dhry:{length} cv32e40p in the shell
        result = subprocess.run(['./scripts/run.sh', 'dhry:' + str(length), 'cv32e40p'], stdout=subprocess.PIPE)
        # parse the shell output for the performance metrics
        # extract the execution time of the benchmark from the line "Total execution time: {exe_time}s" out of all lines in the output
        exe_time_line = [line for line in result.stdout.decode('utf-8').split('\n') if "Total execution time" in line][0]
        exe_time = float(exe_time_line.split(": ")[1].split("s")[0])
        print("execution time = " + str(exe_time) + "s")
        # extract the MIPS value of the benchmark from the line "MIPS (estimated): {mips}" out of all lines in the output
        mips_line = [line for line in result.stdout.decode('utf-8').split('\n') if "MIPS (estimated)" in line][0]
        mips = float(mips_line.split(": ")[1])
        print("MIPS = " + str(mips))
        # extract the num_instr value of the benchmark from the line "CPU Cycles (estimated): {num_instr}" out of all lines in the output
        num_instr_line = [line for line in result.stdout.decode('utf-8').split('\n') if "CPU Cycles (estimated)" in line][0]
        num_instr = float(num_instr_line.split(": ")[1])
        # add the performance metrics to the results list
        results_new_tracegen.append({"length": length, "run": i, "num_instr": num_instr, "exe_time": exe_time, "mips": mips})
    # average the results for the same benchmark length
    avg_num_instr = np.mean([result["num_instr"] for result in results_new_tracegen if result["length"] == length])
    avg_exe_time = np.mean([result["exe_time"] for result in results_new_tracegen if result["length"] == length])
    avg_mips = np.mean([result["mips"] for result in results_new_tracegen if result["length"] == length])
    results_new_tracegen.append({"length": length, "run": "avg", "num_instr": avg_num_instr, "exe_time": avg_exe_time, "mips": avg_mips})

# save the results to a file
with open("results_og_tracegen_no_res_cv32e40p.txt", "w") as file:
    for result in results_og_tracegen:
        file.write(str(result) + "\n")

with open("results_new_tracegen_no_res_cv32e40p.txt", "w") as file:
    for result in results_new_tracegen:
        file.write(str(result) + "\n")

# plot the results
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('Performance metrics of the benchmark')

# Plot MIPS (no perf in red, og tracegen in blue, new tracegen in green)
# make a horizontal line for the max MIPS value of the original tracegen
final_mips_og_tracegen = max([result["mips"] for result in results_og_tracegen if result["run"] == "avg"])
ax.axhline(y=final_mips_og_tracegen, color='b', linestyle='--')
ax.plot([result["num_instr"] for result in results_og_tracegen if result["run"] == "avg"], 
    [result["mips"] for result in results_og_tracegen if result["run"] == "avg"], 'b')
# make a horizontal line for the max MIPS value of the new tracegen
final_mips_new_tracegen = max([result["mips"] for result in results_new_tracegen if result["run"] == "avg"])
ax.axhline(y=final_mips_new_tracegen, color='g', linestyle='--')
ax.plot([result["num_instr"] for result in results_new_tracegen if result["run"] == "avg"], 
    [result["mips"] for result in results_new_tracegen if result["run"] == "avg"], 'g')
ax.set_title('MIPS')
ax.set_xscale('log')
# set y axis to linear scale
ax.set_yscale('linear')
ax.set_xlabel('Benchmark length (number of instructions)')
ax.set_ylabel('MIPS')
ax.grid()
ax.legend(['Original tracegen Max', 'Original tracegen', 'New tracegen without $resolved Max', 'New tracegen without $resolved'])

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# save the plot to a file
fig.savefig("Results_no_resolved_cv32e40p.png")

        