# Multiqueue Simulator, version 1.0
# By Vikram Ravindran
#
# Copyright (C) 2005 Vikram Ravindran
# Please contact the author before using this code

# Tested using Python 2.7.8

# packet record = { probe/nonprobe, location, size, time it leaves location }

# initial probe record (restricted) = { queue that it injects into, number
#of packets, packet size,
# queue record = { time until queue empties, processing rate, output destination]

# wire record = { propagation delay, nonprobe drop probability }

# packet generator record = { queue that it injects into, PDF of size, PDF
#of interarrival time }

import random
import sys

# This provides a deterministic "delta" PDF, for which P[x=val] = 1
def determ(val):
    return val

# The average value of this mix is about 438.5 bytes

def internetmix():
    ds = random.uniform(0,1)
    if(ds<=0.5): return 40.0
    if(ds<=0.63): return round(((ds-0.5)/0.13)*(575.0-40.0)+40.0)
    if(ds<=0.80): return 576.0
    if(ds<=0.83): return round(((ds-0.80)/0.03)*(1499.0-576.0)+576.0)
    if(ds<=1.00): return 1500.0


# Some labels, used in packet data structures

PROBE = 'PROBE'
NONPROBE = 'NONPROBE'


iterations = 500       # Number of dispersion values to run the sim at
iterstep = 5           # Step size of dispersion values 

pktenter = []          # Used to log the times the packets of trains enter
pktleave = []          # Same, but for when they leave

pktqempty = []         # Used to record if probe packets find an empty queue
pktqprobe = []         # Used to record if probe packets find a queue with no
                       #  probes in it
pktqgap = []           # Used to record if a queue became empty

outputstyle = 0       # Outputstyle = 1 means that the simulator will output
                       # (input-time,output-time) pairs, as opposed to the
                       # usual (input-dispersion,output-dispersion)

alldelays = []         # used to record delays that every packet sees
recdelays = 0          # set to 1 if we want delays recorded
numrepeats = 40000     # Number of pairs sent for each dispersion value

numutils = 0

trueUtilAvg = []
adjUtilAvg = []
trueUtilization = []
adjustedUtilization = []

# Used to construct a list of dispersions to iterate over
iterlist = range(0,iterations,iterstep)

#iterlist = []


# Users can select one for statement or the other, depending on whether
# they want to do a multiple-dispersion "chirp" or a single-dispersion probe

#for i in [0.0032]:                     # Probing at a single dispersion
for i in range(0,iterations,iterstep):  # Probing at multiple dispersions
    for j in range(0,numrepeats):
        iterlist.append(i)

# Iterate over all runs
for iter in iterlist:

    # Used to record entering and leaving times of packets for this iteration
    # run alone
    pktecur = []
    pktlcur = []
    pktqey = []
    pktqprb = []
    pktqg = []
   

    # Global clock used to assign times to simulation events
    TIMECLOCK = 0.0

    # Set ENDTIME to -1  to terminate the simulation if there are no probe
    # packets being sent. If you would rather have the simulation run for a
    # period of time, whether probe packets are there or not, set this to the
    # time (in seconds0

    ENDTIME = -1 # 1000000.0

    # GENERAL parameters:
    # 'type': what type the component is (QUEUE, PKTGEN, PROBEGEN or WIRE)
    # 'index': a numerical value used to distinguish components of the same
    #          type
    # 'debug': if set to 1, debug info related to the component will be
    #          displayed
    # 'outputdest': a two-tuple containing the type and number of the 
    #               component that a packet should head to next after
    #               finishing at the current component. An outputdest of
    #               -1 indicates that a packet has reached the end


    # QUEUE parameters:
    # 'procrate': the rate, in bytes per second, that the queue services
    #             a packet
    # '_emptytime_': not a user-defined parameter (hence the underscores).
    #                Its purpose is to record the time at which the queue
    #                will become empty. It is used to calculate the total
    #                waiting time of new packets

    queues = [{}, {}, {}, {}]
    queues[0]['type'] = 'QUEUE'
    queues[0]['index'] = 0
    queues[0]['_emptytime_'] = 0
    queues[0]['_numinqueue_'] = 0
    queues[0]['_numprobes_'] = 0
    queues[0]['_gapoccurred_'] = 0
    queues[0]['procrate'] = (10000000.0/8.0)
    queues[0]['debug'] = 0 # 1
    queues[0]['outputdest'] = -1 # ('QUEUE', 1) 
    queues[0]['dropprob'] = 0.0
    
    queues[1]['type'] = 'QUEUE'
    queues[1]['index'] = 1
    queues[1]['_emptytime_'] = 0
    queues[1]['_numinqueue_'] = 0
    queues[1]['_numprobes_'] = 0
    queues[1]['_gapoccurred_'] = 0
    queues[1]['procrate'] = 5.0
    queues[1]['debug'] = 0 # 1
    queues[1]['outputdest'] = -1 
    queues[1]['dropprob'] = 0.0
   
    
    #queues = [queues[0], queues[1]]
    queues = [queues[0]]

    # PKTGEN parameters
    # sizepdf: A two-tuple, consisting of an RNG function and its parameters,
    #          used to determine the size of generated packets (in bytes)
    # arrivpdf: A two-type, like sizepdf, used to determine the interarrival
    #           times of generated packets to the outputdest
    # _emitted_: Not meant for users to set. Set to 1 if a CT packet has been
    #            created but not yet injected into the system. This prevents
    #            the creation of huge numbers of CT packets which have to wait
    #            around a long time before injection

    pktgens = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]
    
    pktgens[0]['type'] = 'PKTGEN'
    pktgens[0]['index'] = 0
    
   
    # Select a size PDF for the packet generator
    pktgens[0]['sizepdf'] = (internetmix,()) 
    #pktgens[0]['sizepdf'] = (determ,(1000.0,))
    #pktgens[0]['sizepdf'] = (random.expovariate,(1/30.0,)) 



    #pktgens[0]['arrivpdf'] = (random.expovariate,((1/20.0),)) # (random.expovariate,((1/20.0),)) # (determ,(100.0,))
    #pktgens[0]['arrivpdf'] = (random.expovariate,((1/438.5),)) # (random.expovariate,((1/20.0),)) # (determ,(100.0,))
    #pktgens[0]['arrivpdf'] = (random.expovariate,((1/438.5),)) # (random.expovariate,((1/20.0),)) # (determ,(100.0,))


   
    # These values are calculated as follows:
    # Utilization = L*8*X/C
    # Where 8*L is the average size of the cross-traffic distribution, in
    # bits
    # Where X is the parameter of (random.exoivariate,((X),)
    # Where C is the capacity of the queue
    # i.e. 438.5*8*855.1881/10000000 = 0.30

    #pktgens[0]['arrivpdf'] = (random.expovariate,((2822.121),)) # 0.99 util
    #pktgens[0]['arrivpdf'] = (random.expovariate,((2565.564),)) # 0.90 util
    #pktgens[0]['arrivpdf'] = (random.expovariate,((2137.970),)) # 0.75 util
    #pktgens[0]['arrivpdf'] = (random.expovariate,((1995.439),)) # 0.70 util
    #pktgens[0]['arrivpdf'] = (random.expovariate,((1425.314),)) # 0.50 util
    pktgens[0]['arrivpdf'] = (random.expovariate,((855.1881),)) # 0.30 util
    #pktgens[0]['arrivpdf'] = (random.expovariate,((712.657),)) # 0.25 util
    #pktgens[0]['arrivpdf'] = (random.expovariate,((285.0627),)) # 0.10 util

    pktgens[0]['outputdest'] = ('QUEUE', 0) # ('QUEUE', 0)
    pktgens[0]['debug'] = 0 # 1
    pktgens[0]['_emitted_'] = 0


   
    # Another packet generator. We copy all the information from the first,
    # and then alter some parts to suit us
    pktgens[1] = pktgens[0].copy()
    pktgens[1]['index'] = 1
    pktgens[1]['outputdest'] = ('QUEUE', 1)
    pktgens[1]['sizepdf'] = (random.expovariate,(1/10.0,)) # 20
    pktgens[1]['arrivpdf'] = (random.expovariate,((1/20.0),)) # (determ,(100.0,))

    # Cut down pktgens to the appropriate site (however many packet generators
    # we want to use)

    #pktgens = []                                       # no CT
    pktgens = [pktgens[0]]



    # PROBEGEN parameters
    # sizepdf: A two-tuple, consisting of an RNG function and its parameters,
    #          used to determine the size of generated packets (in bytes)
    # arrivpdf: A two-type, like sizepdf, used to determine the interarrival
    #           times of generated packets to the outputdest
    # numpkts: Total number of packets that will be emitted by the probe
    #          generator
    probegens = [{}]
    
    probegens[0]['type'] = 'PROBEGEN'
    probegens[0]['index'] = 0
    probegens[0]['outputdest'] = ('QUEUE', 0)
    probegens[0]['numpkts'] = 2                # two probe packets
    probegens[0]['sizepdf'] = (determ,(1500.0,)) # (determ,(1000.0,))

    probegens[0]['debug'] = 0 # 1

    # We vary the probe packet interarrival time (in essence, the input
    # dispersion) in accordance with the contents of iterlist
    probegens[0]['arrivpdf'] = (determ,(iter*1.0,)) 
    
    #probegens = []       # NO PROBE GENERATORS

    # WIRE parameters
    # propdelay: fixed delay of every packet travelling through the wire
    #            (in other words, the propagation delay)
    wires = [{}]
    wires[0]['type'] = 'WIRE'
    wires[0]['index'] = 0
    wires[0]['propdelay'] = 0.5
    wires[0]['debug'] = 0
    wires[0]['outputdest'] = ('QUEUE', 1)
   

    packets = []            # An array of all packets currently floating
                            # around in the system

    pktserial = 0           # Used to assign unique number to every packet
    
    pendingprobes = 0       # Number of probe packets that have not yet left
                            # the system
  

    # This variable "queueutilized" should be given at least as many elements
    # as there are queues. This should probably be rewritten to run "len" on
    # queues and use the resulting length to set queueutilized
    #queueutilized = [[], [], [], []]
    queueutilized = [[], []]

    # Create all probe packets and set their arrival times into the
    # system
    for i in range(0,len(probegens)):

        # OFFSETTIME is used to provide a delay before the probe packets
        # are injected. It gives a chance for the simulation to get into
        # steady-state

        OFFSETTIME = 0.10
        TMPCLOCK = TIMECLOCK + OFFSETTIME
        while(probegens[i]['numpkts'] > 0):
            pendingprobes += 1
            TMPCLOCK = TMPCLOCK + apply(apply,probegens[i]['arrivpdf'])
            packets.append({'type': 'PROBE', 'location' : ('PROBEGEN',probegens[i]['index']), 'size': apply(apply,probegens[i]['sizepdf']), 'serial': pktserial, 'wtime': TMPCLOCK, 'delays': [('PROBE')], 'qempty': [('PROBE')], 'qprobe': [('PROBE')], 'qgap': [('PROBE')]})
            probegens[i]['numpkts'] -= 1
            pktserial = pktserial + 1
            if(probegens[i]['debug']): print "(ITER "+`iter`+") PROBE SOURCE "+`i`+" EMITTED PACKET "+`pktserial-1`


    while 1:   # event loop for a given simulation

        # Create new packets for all packet generators whose old packets have
        # already entered the system
        for i in range(0,len(pktgens)):
            # If there isn't a cross-traffic packet waiting to be emitted,
            # create one (we do this to ensure that a new cross-traffic packet
            # isn't created with each iteration of the event loop---rather, we
            # wait until the previous one is injected. This ensures that
            # packets have the correct interpacket spacing
            if(pktgens[i]['_emitted_'] == 0):
                packets.append({'type': 'NONPROBE', 'location' : (pktgens[i]['type'],pktgens[i]['index']), 'size': apply(apply,pktgens[i]['sizepdf']), 'serial': pktserial, 'wtime': TIMECLOCK+apply(apply,pktgens[i]['arrivpdf']), 'delays': [('NONPROBE')], 'qempty': [('NONPROBE')], 'qprobe': [('NONPROBE')], 'qgap': [('NONPROBE')]})
                pktgens[i]['_emitted_'] = 1
                pktserial = pktserial + 1
                if(pktgens[i]['debug']): print "(ITER "+`iter`+") CT SOURCE "+`i`+" EMITTED PACKET "+`pktserial-1`+" AT TIME "+`packets[-1]['wtime']`
   

       
        # Find packet with the lowest wtime (finishing time)
        mintime = 999999999
        minidx = -1
        
        for i in range(0,len(packets)):
            if(packets[i]['wtime'] < mintime):
                mintime = packets[i]['wtime']
                minidx = i
   
        # If there are no packets left, we've reached the end
        if minidx == -1: break

        # If we are running the sim by watching the probe packets, stop the
        # sim once the packets have left
        if (ENDTIME == -1 and pendingprobes == 0): break
        # Otherwise, stop the sim once time runs out
        if (ENDTIME > -1 and TIMECLOCK > ENDTIME): break

        # Set clock to the finishing time of the selected packet
        TIMECLOCK = mintime
    
        minpkt = packets[minidx]
    
        # Perform action based on current location of selected packet
        queueidx = minpkt['location'][1]

        # If the packet is located in a queue, move it to the next location
        # If there is no next location, remove it from the list of packets
        # If the packet was a probe packet, record the time of leaving, and
        # subtract 1 from the number of pending probes
        if(minpkt['location'][0] == 'QUEUE'):
             queues[queueidx]['_numinqueue_'] -= 1
             if(minpkt['type'] == 'PROBE'): queues[queueidx]['_numprobes_'] -= 1
             if(queues[queueidx]['_numinqueue_']==0): 
                 queueutilized[queueidx][-1].append(TIMECLOCK)
                 queues[queueidx]['_gapoccurred_'] = 1
             if recdelays == 1: 
                 packets[minidx]['delays'][-1][1] = TIMECLOCK - packets[minidx]['delays'][-1][1]

             if(queues[queueidx]['outputdest'] == -1):
                 if(queues[queueidx]['debug']): print "(ITER "+`iter`+") TIME "+`TIMECLOCK`+" ("+minpkt['type']+") Packet "+`minpkt['serial']`+" left"
                 if(minpkt['type'] == 'PROBE'): 
                     pendingprobes -= 1
                     pktlcur.append(TIMECLOCK)
                     pktqey.append(packets[minidx]['qempty'])
                     pktqprb.append(packets[minidx]['qprobe'])
                     pktqg.append(packets[minidx]['qgap'])
                 if recdelays == 1: alldelays.append(packets[minidx]['delays'])

                 packets.remove(packets[minidx])
                 continue
             else:
                 if(minpkt['type'] == 'NONPROBE' and random.uniform(0,1) < queues[queueidx]['dropprob']):
                     packets.remove(packets[minidx])
                 else:
                     packets[minidx]['location'] = queues[queueidx]['outputdest']
        elif(minpkt['location'][0] == 'WIRE'):
             # Move the packet to the location that the wire is connecting to
             packets[minidx]['location'] = wires[queueidx]['outputdest']
        elif(minpkt['location'][0] == 'PKTGEN'):

             # Since the packet is being emitted from the PKTGEN, set its
             # emitted value to zero
             pktgens[minpkt['location'][1]]['_emitted_'] = 0

             # Inject the packet into whatever the packet generator is
             # connected to. Set _emitted_ to 0, meaning that the generator
             # can create a new packet
             packets[minidx]['location'] = pktgens[queueidx]['outputdest']
        elif(minpkt['location'][0] == 'PROBEGEN'):
             # Inject a probe packet into the system. Record time of entry.
             packets[minidx]['location'] = probegens[queueidx]['outputdest']
             pktecur.append(TIMECLOCK)
      

        # Perform action based on new location of selected packet
        if(packets[minidx]['location'][0] == 'QUEUE'):
             queueidx = packets[minidx]['location'][1]

             packets[minidx]['qgap'].append(queues[queueidx]['_gapoccurred_'])

             # Here we record all the times that the queue became empty 

             if(queues[queueidx]['_numinqueue_']==0): 
                 packets[minidx]['qempty'].append((queueidx,1))
             else:
                 packets[minidx]['qempty'].append((queueidx,0))

             if(queues[queueidx]['_numprobes_']==0): 
                 packets[minidx]['qprobe'].append((queueidx,1))
             else:
                 packets[minidx]['qprobe'].append((queueidx,0))

             # If there are no packets in a queue, record the time (useful so
             # we can calculate the utilization)
             if(queues[queueidx]['_numinqueue_']==0): queueutilized[queueidx].append([TIMECLOCK])
             queues[queueidx]['_numinqueue_'] += 1
             if(minpkt['type'] == 'PROBE'): 
                 queues[queueidx]['_numprobes_'] += 1
                 queues[queueidx]['_gapoccurred_'] = 0

             # Add new list and record time of entry to queue
             if(recdelays==1): 
                 packets[minidx]['delays'].append([(queueidx,),TIMECLOCK])

             if(queues[queueidx]['debug']): print "(ITER "+`iter`+") TIME "+`TIMECLOCK`+": ("+packets[minidx]['type']+") Packet "+`packets[minidx]['serial']`+" entering queue "+`queueidx`

             # Calculate transmission time of the packet (based on its size
             # and the transmission rate of the queue server)
             transtime = packets[minidx]['size']/queues[queueidx]['procrate']

             # If the queue had become empty before our arrival, set the
             # empty time to the current time (since the queue is empty now, too

             if(queues[queueidx]['_emptytime_'] < TIMECLOCK):
                 queues[queueidx]['_emptytime_'] = TIMECLOCK

             # Add the transmission time of the newly-arrived packet to the
             # empty-time (after the old empty time, the queue won't be empty,
             # but will have one remaining packet: the new packet. By adding
             # the transmission time of the new packet, we get an accurate
             # empty time)

             queues[queueidx]['_emptytime_'] += transtime

             # Set finishing time of packet to the current empty-time of the
             # queue
             packets[minidx]['wtime'] = queues[queueidx]['_emptytime_']
           
        elif(minpkt['location'][0] == 'WIRE'):
             # If the packet is now in a wire, set its finishing time to the
             # current time, plus the propagation delay
             wireidx = minpkt['location'][1]
             packets[minidx]['wtime'] = TIMECLOCK + wires[wireidx]['propdelay']


    # AT THIS POINT, A SINGLE SIMULATION RUN HAS ENDED

    numqueues = len(queues)
    utilizedrun = [0.0]*numqueues
    trueUtilization = [0.0]*numqueues
    adjustedUtilization = [0.0]*numqueues



    # If we recorded a start time for the queue being utilized and not the end
    # time, set the end time to the end of the simulation (since the simulation
    # is now over)

    for i in range(0,numqueues):
        if(len(queueutilized[i]) > 0 and len(queueutilized[i][-1]) < 2): queueutilized[i][-1].append(TIMECLOCK)


    # The total length of the simulation is equal to the time at which the
    # simulation was stopped (since the simulation always starts at time 0)

    totalrun = TIMECLOCK

    # Calculate the total time that each queue i was utilized

    for i in range(0,numqueues):
        for j in queueutilized[i]:
            utilizedrun[i] += (j[1] - j[0])

    # Calculate both true utilization (which includes the probe packets)
    # and the "adjusted" utilization (which doesn't include the probe
    # packets---i.e., in theory it would be the utilization if the probe
    # packets weren't there). These values are calculated for a particular
    # run

    for i in range(0,numqueues):
        trueUtilization[i] = (utilizedrun[i]/totalrun)
        probetime = 2*probegens[0]['sizepdf'][1][0]/queues[i]['procrate']
        adjustedUtilization[i] = ((utilizedrun[i]-probetime)/totalrun)

    # Store the utilizations in corresponding "average" values---these will
    # be used to calculate a utilization average over all runs

    if(numutils == 0):
        trueUtilAvg = trueUtilization[:]
        adjUtilAvg = adjustedUtilization[:]
        numutils = 1
    else:
        for i in range(0,numqueues):
            trueUtilAvg[i] += trueUtilization[i]
            adjUtilAvg[i] += adjustedUtilization[i]
        numutils += 1

    # Record entry and leaving times of the packets in this iteration (i.e. of
    # this particular run) 

    pktenter.append(pktecur)
    pktleave.append(pktlcur)
    pktqempty.append(pktqey)
    pktqprobe.append(pktqprb)
    pktqgap.append(pktqg)
    #print pktqgap
    # Calculate utilization

    # Flush stdout, so that all pending debug messages will be printed
    sys.stdout.flush()


# AT THIS POINT, _ALL_  RUNS HAVE ENDED

# packet record = { probe/nonprobe, location, size, time it leaves location }


# Count number of packet records
pktarrlen = len(pktenter)

# Print them out in one of two styles:
# If outputstyle is set to 1, print out packet times in 
# (entering time, leaving time) format
# If outputstyle is set otherwise, print out packet times in
# (initial dispersion, final dispersion) format
# (note: the latter assumes packet pairs right now...please fix)

for i in range(0,pktarrlen):
    if(outputstyle==1):
        print pktenter[i][0],pktleave[i][0]
        print pktenter[i][1],pktleave[i][1]
    elif(outputstyle==0):
       print "%0.10f %0.10f" % ((pktenter[i][1] - pktenter[i][0]), (pktleave[i][1] - pktleave[i][0])),
       print " ",pktqprobe[i][0][1][1]," ",pktqprobe[i][1][1][1], " -"+`pktqgap[i][1][1]`


# Calculate average of utilizations over all runs

for i in range(0,numqueues):
    trueUtilAvg[i] = trueUtilAvg[i]/numutils
    adjUtilAvg[i] = adjUtilAvg[i]/numutils

print "TRUE UTILIZATION (incl. probe packets): ",trueUtilAvg
print "ADJUSTED UTILIZATION: ",adjUtilAvg
print "TIMECLOCK: ",TIMECLOCK

# If the user wanted all delays to be recorded (by setting recdelays to 1)
#  display them

if recdelays == 1:

    numdelays = 0
    sumdelays = 0
    
    for i in alldelays:
        if(i[0] == 'NONPROBE'):
           subarr = i[1:]
           for j in subarr:
               numdelays = numdelays + 1
               print j[1] # j[0][0], j[1]
               sumdelays = sumdelays + j[1]
     
    sys.stderr.write("((("+`sumdelays/(numdelays*1.0)`+")))\n")
    sys.stderr.write("Total number of packets: "+`numdelays`)


