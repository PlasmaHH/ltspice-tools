#!/usr/bin/python3

import argparse
import sys

outfile = None
verbose = False

def output( s ):
    outfile.write(s + "\n")
    if( verbose ):
        print(s)

def split_quoted( s, d = None):
    if( s.find('"') == -1  ):
        return s.split(d)
    ret = []
    inquote = False

    nstr=""
    for c in s:
        if( inquote ):
            if( c == '"' ):
                inquote = False
            nstr += c
        elif( c.isspace() ):
            if( len(nstr) > 0 ):
                ret.append(nstr)
                nstr = str()
            # else just ignore
        elif( c == '"' ):
            inquote = True
            nstr += c
        else:
            nstr += c
    if( len(nstr) > 0 ):
        ret.append(nstr)

    return ret

# borrowed from vdb
def format_line( line, maxsz, padbefore, padafter ):
    ret = ""
    cnt = 0
    for cell in line:
        if( cell is None ):
            cell = ""
#        ret += str(maxsz[cnt])
        ret += padbefore
        if isinstance(cell,tuple):
            cval = cell[0]
            clen = cell[1]
            if( len(cell) > 2 ):
                if( cell[2] == 0 ):  # truncate to max size
                    cval = cval[0:maxsz[cnt]]
            if( len(cell) > 1 ):
                if( isinstance(clen,str) ):
                    import vdb.color
                    v=cell[0]
                    c=cell[1]
                    cell = vdb.color.colorl(cval,clen) + cell[2:]
                    cval = cell[0]
                    clen = cell[1]
            if( clen == 0 ):
                clen = len(cval)
                xpad = maxsz[cnt] - clen
            else:
                xpad = maxsz[cnt] - clen
            if( cnt+1 == len(line) ):
                xpad = 0
            ret += f"{cval}{' ' * xpad}"
        else:
            xmaxsz = maxsz[cnt]
            if( cnt+1 == len(line) ):
                xmaxsz = 0
            ret += "{cell:<{maxsz}}".format(cell = cell, maxsz = xmaxsz )
        ret += padafter
        cnt += 1
    return ret

def format_table( tbl, padbefore = " ", padafter = " " ):
    ret = ""
    if( len(tbl) == 0 ):
        return ret
#    maxsz = list(itertools.repeat(0,len(tbl[0])))
    maxsz = {}
#    print("len(maxsz) = '%s'" % len(maxsz) )
    for line in tbl:
#        print("line = '%s'" % line )
        cnt = 0
#        for cell in line:
        for cnt in range(0,len(line)):
            cell = line[cnt]
            if( cell is None ):
                cell=""
#            print("cnt = '%s'" % cnt )
            if isinstance(cell,tuple):
                if( len(cell) == 2 ):
                    clen = cell[1]
                    if( isinstance(clen,str) ):
                        clen = len(cell[0])
                    maxsz[cnt] = max(maxsz.get(cnt,0),clen)
                elif( len(cell) > 3):
                    maxsz[cnt] = max(maxsz.get(cnt,0),cell[3])
                else:
                    # Ignore the size at that point
                    maxsz[cnt] = max(maxsz.get(cnt,0),1)
            else:
                maxsz[cnt] = max(maxsz.get(cnt,0),len(str(cell)))
#            cnt += 1
#    for x,y in maxsz.items():
#        print("x = '%s'" % x )
#        print("y = '%s'" % y )
    for line in tbl:
        ret += format_line(line,maxsz,padbefore,padafter)
        ret += "\n"
    return ret

def print_table ( tbl, padbefore = " ", padafter = " " ):
    ret = format_table( tbl, padbefore, padafter )
    print(ret)
    return ret


def random( dist : str ):
    pass

def split_suffix( value ):
    match value[-1]:
        case "n" | "u" | "m" | "f" | "p" | "µ" | "k":
            return ( value[:-1], value[-1] )
    if( value.endswith("Meg") ):
        return ( value[:-3], value[-3] )
    return ( value, None )

class position:
    def __init__( self, x, y, rot ):
        self.x = x
        self.y = y
        self.rot = rot

    def __str__( self ):
        return f"{self.x} {self.y} {self.rot}"

class line:

    def __init__( self ):
        self.raw = None

class raw_line(line):

    def __init__( self, line ):
        self.line = line
        self.raw = True

    def generate( self ):
        output( " ".join(self.line) )

next_bit_id = 0

def gen_bit_id( ):
    global next_bit_id

    ret = next_bit_id
    next_bit_id += 1
    return ret

num_tolstrings = 0

class symbol(line):
    valid_lines = { "WINDOW" }
    shortmap = { "cap" : "C", "res" : "R", "ind" : "I", "ind2" : "I", "voltage" : "V" }
    valid_extra = { "cap" : { "Rser", "Rpar", "Lser", "Lpar" } }
    def __init__( self, typ, pos ):
        self.typ = typ # SYMATTR first parameter
        self.short = self.shortmap.get(typ,None)
        self.pos = pos
        self.attributes = {}
        self.lines = []
        self.name = None  # SYMATTR InstName    - Will identify the component
        self.value = None # SYMATTR Value       - Will be changed to reflect one of the MC values
        self.value2 = None # Overwritten by us 
        self.spicelines = {}
        self.raw = False

    def generate( self ):
        output(f"SYMBOL {self.typ} {self.pos}")
        for line in self.lines:
            output( " ".join(line) )
        output(f"SYMATTR InstName {self.name}")
        if( self.value is not None ):
            output(f"SYMATTR Value {self.value}")
        if( self.value2 is not None ):
            output(f"SYMATTR Value2 {self.value2}")
        if( len(self.spicelines) > 0 ):
            spstr = "SYMATTR SpiceLine"
            for k,v in self.spicelines.items():
                spstr += f" {k}={v}"
            output(spstr)

    def spice( self, key ):
        return self.spicelines.get(key,None)

    def extract_info( self, line ):
        match line[0]:
            case "InstName":
                self.name = line[1]
            case "Value":
                self.value = " ".join(line[1:])
            case "Value2":
                self.value2 = " ".join(line[1:])
            case "SpiceLine":
                for sl in line[1:]:
                    sl = sl.split("=")
                    self.spicelines[sl[0]] = sl[1]
            case _:
                print("no info: '%s'" % (line,) )

    def add_info( self, line ):
        match line[0]:
            case "SYMATTR":
                self.attributes[line[1]] = line[2:]
                self.extract_info(line[1:])
            case item if item in self.valid_lines:
                self.lines.append(line)
            case _:
                return False
        return True

    def mc_tolstr( self, value, tolmin, tolmax ):
        return f"{{mc_tolerance({value},{tolmin:.8},{tolmax:.8},{{flat(1)}})}}"

    def minmax_tolstr( self, value, tolmin, tolmax ):
        bid = gen_bit_id()
        return f"{{selected_tolerance({bid},{value},{tolmin},{tolmax})}}"

    def both_tolstr( self, value, tolmin, tolmax ):
        mc = self.mc_tolstr(value,tolmin,tolmax)
        mm = self.minmax_tolstr(value,tolmin,tolmax)
        return f"{{if(bit_run < 0, {mc}, {mm} )}}"

    def get_tolstr( self, mc, mm, value, tolmin, tolmax ):
        global num_tolstrings
        num_tolstrings += 1
#        print(f"get_tolstr(self,{mc},{mm},{value},{tolmin},{tolmax})")
        if( mc and mm ):
            return self.both_tolstr( value, tolmin, tolmax )
        elif( mc ):
            return self.mc_tolstr( value, tolmin, tolmax )
        elif( mm ):
            return self.minmax_tolstr( value, tolmin, tolmax )

    def value_tolerance( self, tol, mc, mm ):
        try:
#            print("self.value = '%s'" % (self.value,) )
            value,_ = split_suffix(self.value)
            value = float(value)
        except ValueError:
            print(f"Don't know what {self.value} means")
            return
        tol = float(tol)/100.0
        tolstr = self.get_tolstr(mc,mm,self.value,tol,tol)
        if( self.typ in { "voltage", "ind2" } ):
            self.value = tolstr
        else:
            self.value2 = tolstr
        #todo record changes and output table at the end

    def gen_tolerances( self, tol, mc, mm ):
#        print("self.name = '%s'" % (self.name,) )
#        print("tol = '%s'" % (tol,) )
#        print("self.spicelines = '%s'" % (self.spicelines,) )
        if( isinstance(tol,float) ):
            self.value_tolerance(tol,mc,mm)
            print()
            return
        for t in tol:
            t = t.split(":")
            if( len(t) != 2 ):
                print(f"Invalid input {t}")
                continue
#            print("t = '%s'" % (t,) )
            if( t[0] == self.shortmap.get(self.typ,None) ):
                self.value_tolerance(t[1],mc,mm)
            else:
                tf,tv = t
                sidx = tv.find("/")
                if( sidx != -1 ):
                    tv = tv.split("/")
                    tva = float(tv[0])/100.0
                    tvb = float(tv[1])/100.0
                else:
                    tva = tvb = float(tv)/100.0
                oldval = self.spicelines.get(tf,None)
                if( oldval is not None ):
#                    print(f"{tf} is in spice lines")
                    ntv = self.get_tolstr(mc,mm,oldval,tva,tvb)
#                    print(f"{tva:.8}/{tvb:.8} => {ntv}")
                    self.spicelines[tf] = ntv
        print()


"""

min/max are created by:

# part tolerance ( can be different +/- )
# global part tolerance
# global additional tolerance-shift (can be -5%/-2% or so to simulate all being lower)

# step through all parameterts min/max values

.step param InstName list <min> <max>

or through the nominal value too (2**N or 3**N steps in total)

.step param InstName list <min> <nominal> <max>

We could use the binary hack in
https://www.analog.com/en/technical-articles/ltspice-worst-case-circuit-analysis-with-minimal-simulations-runs.html but
that doesn't gain us anything ( we generate a file, doesn't care how ugly it is) and I don't know how to get to the
tolerance field of the part itself there. Also we can use it better as a starting point to narrow down things or exclude
values that we have settled on to speed up calculation. If at all we would need to make it take assymetric tolerances.

# step through random values. Different distributions?
Create a function and replace every value with mcv( value, tolerance_min, tolerance_max )

for all functions/params etc. try to avoid name clashes so maybe do __ltmc_ in front of every



# add option to add usual "high precision" options like numdgt, reltol and plotwinsize. Maybe add some options to enable
# gear and matrix optimizations if possible

# Later on add some tools to add good .measure and .plot commands for intresting things to run automatically 




"""

class spice_line:
    def __init( self, line ) :
        self.line = line
    
valid_singles = {
        "Version", # usually 4
        "SHEET",   # Probably with size
        "WIRE",    # straight wire with start and end
        "TEXT",    # text executed as command
        "FLAG",    # ground symbol
        }

symbol_by_type = {}

def store_symbol( all, symbol ):
    all.append(symbol)
    global symbol_by_type
    syms = symbol_by_type.setdefault( symbol.typ, [] )
    syms.append(symbol)

encoding = "iso8859_15" # latin9

def parse_asc( fname ):
    print(f"Analyzing {fname}...")
    all = []
    with open(fname,"r",encoding=encoding) as f:
        current_symbol = None
        for line in f.readlines():
            line=line.rstrip()
#            line = line.split()
            line = split_quoted(line)
            match line[0]:
                case "SYMBOL":
                    if( current_symbol is not None ):
                        store_symbol(all,current_symbol)
                    current_symbol = symbol(line[1], position( line[2], line[3], line[4] ))
                case item if item in valid_singles:
                    if( current_symbol is not None):
                        store_symbol(all,current_symbol)
                        current_symbol = None
                    all.append(raw_line(line))
                case _:
                    if( current_symbol is not None ):
                        if( current_symbol.add_info(line) is False ):
                            print(f"Unknown line {line[0]}")
                    else:
                        print(f"Unknown line {line[0]}")
                        all.append(raw_line(line))
        if( current_symbol is not None ):
            store_symbol(all,current_symbol)


    return all

# only for supported types
type_tr = {
        "res"     : "Resistor",
        "cap"     : "Capacitor",
        "ind"     : "Inductor",
        "ind2"    : "Inductor",
        "voltage" : "Voltage",
        }

def show_overview( ):
    tbl = []
    print("Supported Component Overview:")
    tbl.append( [ "Component", "Total", "Name", "With tolerances" ] )
    for k,vl in symbol_by_type.items():
        notol = []
        tol = []
        for c in vl:
            stol = c.spice("tol")
            if( stol is not None ):
                tol.append(f"{c.name}[{stol}%]")
            else:
                notol.append(c.name)


        typ = type_tr.get(k,None)
        if( typ is not None ):
            tbl.append( [ typ, len(vl), ",".join(notol), ",".join(tol)] )
    print_table(tbl)

def selected( sym, capacitors, resistors, inductors, components ):
#    print("sym = '%s'" % (sym,) )
#    print("resistors = '%s'" % (resistors,) )
    if( sym.raw ):
        return None
    comp = components.get(sym.name,None)
    if( comp is not None ):
        return comp
    match sym.typ:
        case "cap":
            return capacitors
        case "res":
            return resistors
        case "ind":
            return inductors
        case "ind2":
            return inductors
    return None

def generate_bitfunctions( ):
    ret = """
TEXT 0 0    Left 2 !.function selected_tolerance( idx, nominal, tolerancemin, tolerancemax ) { if( selected(idx), nominal*tolerancemin, nominal*tolerancemax ) }
TEXT 0 -40  Left 2 !.function shift_i( num, x )   { floor(shift_d(num,x)) }
TEXT 0 -80  Left 2 !.function shift_d( num, x )   { num / (2**x) }
TEXT 0 -120 Left 2 !.function bit_set( num, bit ) { shift_d(num, bit+1) - shift_i(num, bit+1) >= 0.5 }
TEXT 0 -160 Left 2 !.function selected( idx )     { bit_set( bit_run, idx ) }
TEXT 0 -200 Left 2 !.function mc_tolerance( nominal, tolerancemin, tolerancemax,rnd ) { nominal + nominal * ( ( (tolerancemin+tolerancemax) * ( (rnd+1)/2 ) ) - tolerancemin ) }
"""
    return ret

def main ( ):

    parser = argparse.ArgumentParser(description='Create MonteCarlo like Simulations out of ordinary ones', fromfile_prefix_chars="@", formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=32))
                                     #,formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    parser.add_argument("file", help = ".asc input file")
    parser.add_argument("-O","--omit-optimizations", action = "store_true", help = "Omit all result accuracy options" )
    parser.add_argument("-v","--verbose", action = "store_true", help = "Be quite verbose" )

    generic = parser.add_argument_group("Generic Component Handling", "All these take a tolerance in %% which is applied to all specified parameters of a component, e.g. serial/parallel resistance of caps etc.. Leave them empty to only apply tolerances mentioned in the model ( via tol=xxx SpiceLine )")

    generic.add_argument("-c","--capacitors", metavar="CAP",type=float, action="store", help = "Capacitor tolerance for everything")
    generic.add_argument("-r","--resistors",  metavar="RES",type=float, action="store", help = "Resistor tolerance for everything")
    generic.add_argument("-i","--inductors",  metavar="IND",type=float, action="store", help = "Inductor tolerance for everything")
    generic.add_argument("-a","--all",        type=float, action="store", help = "Tolerance in %% for all supported types that don't have an explicit tolerance")
#    generic.add_argument("-","--", action="store_true", help = "")

    algo = parser.add_argument_group("Algorithm Parameters", "You can specify -m and -M together but be aware that this can cause extreme amount of steps")
    algo.add_argument("-m","--monte-carlo", action = "store_true", help = "Do a monte carlo simulation by chosing random values within the tolerance range")
    algo.add_argument("-M","--min-max",     action = "store_true", help = "Do every combination of min/max values, which results in 2^N steps for N components")
    algo.add_argument("-d","--distribution",action = "store", choices = [ "flat", "gauss"], default = "", help = "Distribution to derive the value from nominal and tolerance.")
#    algo.add_argument("-dp","--dist-param", action = "store", metavar="DP", help = "Distribution specific parameters (see code or documentation))" )
    algo.add_argument("-R","--runs", action="store", help = "For the monte carlo variant, specify the number of runs to do")

    # Used/Useful ltspice functions: ( To Have different number per run tick the seed option in hacks )
    # flat(x) -x to x float
    # gauss(x) gauss distribution on sigma x ...  Problem here is we don't really know the distribution perfectly and
    # all we have a is a tolerance. Until we understand the involved maths and manufacturing processes better we settle
    # for some hand selected values here:
    # gauss(0,3) should give us a nice -1 ... 1 distribution that looks somewhat realistic. Still we could get the
    # occasional outlier. Should we therefore clamp this maybe? hm... .function t_gauss() { limit(gauss(0.3),1,-1) }

    # note useful (here):
    # rand(x) just depends on integer x. Usually time * scaling factor to have a different number per timestep ("rise"
    # times unclear). Depends on time steps too.
    # random(x) like rand but takes a float that tells how to "smooth" between the int plateus.

    single = parser.add_argument_group("Single Component Selections","Use these options to select single components and get more control over them. Consider using @fromfiles for your options")
    single.add_argument("-C","--component", type = str, default = "", help = "Component designator e.g. R0=R:0.4;Cpar=1 (see code or documentation)" )
    # select components and for each
    # - when nothing is selected, tolerance on all values
    #   -C R0,R2,R3
    # - select values for all of them
    #   -C R0=4.5,R2=5.6
    # - select values for a single one
    #   -C R0=R:0.5,L4=I:1;Rser:3;Lser:1,C3=C:10/40;Rser=1

    
    args = parser.parse_args(sys.argv[1:])

    global verbose
    verbose = args.verbose

    all = parse_asc( args.file )
    outfilename = args.file.replace(".asc",".mc.asc")


    if( outfilename == args.file ):
        outfilename += ".mc"

    global outfile
    outfile = open(outfilename,"w",encoding=encoding)

    show_overview( )
    if( args.monte_carlo is False and args.min_max is False ):
        print("You need to chose -m or -M or both to make me do something")
        return None
    
    ecom = args.component.split(",")

    components = {}
    for e in filter(len,ecom):
        comp,tol = e.split("=")
        components[comp] = tol.split(";")

    if( args.all ):
        if( args.capacitors is None ):
            args.capacitors = args.all
        if( args.resistors is None ):
            args.resistors = args.all
        if( args.inductors is None ):
            args.inductors = args.all


    for sym in all:
        tol = selected( sym, args.capacitors, args.resistors, args.inductors, components )
        if( tol is not None ):
            sym.gen_tolerances( tol, args.monte_carlo, args.min_max  )



    for a in all :
        a.generate()

    output( generate_bitfunctions()  )
    maxbit = 1 << next_bit_id
#    print("maxbit = '%s'" % (maxbit,) )
#    print("args.min_max = '%s'" % (args.min_max,) )
#    print("args.monte_carlo = '%s'" % (args.monte_carlo,) )
#    print("args.runs = '%s'" % (args.runs,) )
    if( args.runs is not None ):
        if( args.min_max ):
            if( args.monte_carlo ):
                output( f"TEXT 0 -240 Left 2 !.step param bit_run -{args.runs} {maxbit} 1" )
            else:
                output( f"TEXT 0 -240 Left 2 !.step param bit_run 0 {maxbit} 1" )
        else:
            output( f"TEXT 0 -240 Left 2 !.step param mc_run 1 {args.runs} 1" )
    elif( args.min_max ):
        output( f"TEXT 0 -240 Left 2 !.step param bit_run 0 {maxbit} 1" )
    else:
        print("You did not specify any -R run number, this only works when you run the simulation multiple times. Make sure you have a .step param or use -R")

    if( maxbit > 100001 ):
        print(f"Too many iterations ({maxbit}), ltspice only supports up to 100001. It would probably take too long anyways. Try to reduce the number of components used, or switch to monte carlo instead")
    print(f"Written output to {outfilename}")
    print(f"Generated {num_tolstrings} tolerance modifiers")

if __name__ == "__main__":
    main()

# vim: tabstop=4 shiftwidth=4 expandtab ft=python
