import Tkinter as tk
from Tkinter import *
import PIL.Image
import tkMessageBox
import tkFont,tkFileDialog
import shlex
import MLN
import subprocess
import configMLN as config1
from ScrolledText import *
import os
import time
import pickle


def config_value(key, default):
    if key in dir(config1):
        return eval("config1.%s" % key)
    return default

def call(args):
    try:
        subprocess.call(args)
    except:
        args = list(args)
        args[0] = args[0] + ".bat"
        subprocess.call(args)
class MLNInfer(object):
    def __init__(self):
        self.pymlns_methods = MLN.InferenceMethods.getNames()
        self.alchemy_methods = {"MC-SAT": "-ms", "Gibbs sampling": "-p", "simulated tempering": "-simtp",
                                "MaxWalkSAT (MPE)": "-a", "belief propagation": "-bp"}
        self.jmlns_methods = {"MaxWalkSAT (MPE)": "-mws", "MC-SAT": "-mcsat", "Toulbar2 B&B (MPE)": "-t2"}
        self.alchemy_versions = config1.alchemy_versions
        self.default_settings = {"numChains": "1", "maxSteps": "", "saveResults": False, "convertAlchemy": False,
                                 "openWorld": True}  # a minimal set of settings required to run inference

    def run(self, mlnFiles, evidenceDB, method, queries, engine="PyMLNs", output_filename=None, params="", **settings):
        '''
            runs an MLN inference method with the given parameters

            mlnFiles: list of one or more MLN input files
            evidenceDB: name of the MLN database file from which to read evidence data
            engine: either "PyMLNs"/"internal", "J-MLNs" or one of the keys in the configured Alchemy versions (see configMLN.py)
            method: name of the inference method
            queries: comma-separated list of queries
            output_filename (compulsory only when using Alchemy): name of the file to which to save results
                For the internal engine, specify saveResults=True as an additional settings to save the results
            params: additional parameters to pass to inference method. For the internal engine, it is a comma-separated
                list of assignments to parameters (dictionary-type string), for the others it's just a string of command-line
                options to pass on
            settings: additional settings that control the inference process, which are usually set by the GUI (see code)

            returns a mapping (dictionary) from ground atoms to probability values.
                For J-MLNs, results are only returned if settings are saved to a file (settings["saveResults"]=True and output_filename given)
        '''
        self.settings = dict(self.default_settings)
        self.settings.update(settings)
        input_files = mlnFiles
        db = evidenceDB
        query = queries

        results_suffix = ".results"
        output_base_filename = output_filename
        if output_base_filename[-len(results_suffix):] == results_suffix:
            output_base_filename = output_base_filename[:-len(results_suffix)]

        # determine closed-world preds
        cwPreds = []
        if "cwPreds" in self.settings:
            cwPreds = filter(lambda x: x != "", map(str.strip, self.settings["cwPreds"].split(",")))
        haveOutFile = False
        results = None

        # engine-specific handling
        if engine in ("internal", "PyMLNs"):
            try:
                print "\nStarting %s...\n" % method

                # read queries
                queries = []
                q = ""
                for s in map(str.strip, query.split(",")):
                    if q != "": q += ','
                    q += s
                    if MLN.balancedParentheses(q):
                        queries.append(q)
                        q = ""
                if q != "": raise Exception("Unbalanced parentheses in queries!")

                # create MLN
                verbose = True
                mln = MLN.MLN(input_files, verbose=verbose, defaultInferenceMethod=MLN.InferenceMethods.byName(method))

                # set closed-world predicates
                for pred in cwPreds:
                    mln.setClosedWorldPred(pred)

                # create ground MRF
                mrf = mln.groundMRF(db, verbose=verbose)

                # collect inference arguments
                args = {"details": True, "verbose": verbose, "shortOutput": True, "debugLevel": 1}
                args.update(eval("dict(%s)" % params))  # add additional parameters
                if args.get("debug", False) and args["debugLevel"] > 1:
                    print "\nground formulas:"
                    mrf.printGroundFormulas()
                    print
                if self.settings["numChains"] != "":
                    args["numChains"] = int(self.settings["numChains"])
                if self.settings["maxSteps"] != "":
                    args["maxSteps"] = int(self.settings["maxSteps"])
                outFile = None
                if self.settings["saveResults"]:
                    haveOutFile = True
                    outFile = file(output_filename, "w")
                    args["outFile"] = outFile
                args["probabilityFittingResultFileName"] = output_base_filename + "_fitted.mln"

                # check for print/write requests
                if "printGroundAtoms" in args:
                    if args["printGroundAtoms"]:
                        mrf.printGroundAtoms()
                if "printGroundFormulas" in args:
                    if args["printGroundFormulas"]:
                        mrf.printGroundFormulas()
                if "writeGraphML" in args:
                    if args["writeGraphML"]:
                        graphml_filename = output_base_filename + ".graphml"
                        print "writing ground MRF as GraphML to %s..." % graphml_filename
                        mrf.writeGraphML(graphml_filename)

                # invoke inference and retrieve results
                mrf.infer(queries, **args)
                results = {}
                for gndFormula, p in mrf.getResultsDict().iteritems():
                    results[str(gndFormula)] = p

                # close output file and open if requested
                if outFile != None:
                    outFile.close()
            except:
                cls, e, tb = sys.exc_info()
                sys.stderr.write("Error: %s\n" % str(e))
                traceback.print_tb(tb)

        elif engine == "J-MLNs":  # engine is J-MLNs (ProbCog's Java implementation)

            # create command to execute
            app = "MLNinfer"
            params = [app, "-i", ",".join(input_files), "-e", db, "-q", query,
                      self.jmlns_methods[method]] + shlex.split(params)
            if self.settings["saveResults"]:
                params += ["-r", output_filename]
            if self.settings["maxSteps"] != "":
                params += ["-maxSteps", self.settings["maxSteps"]]
            if len(cwPreds) > 0:
                params += ["-cw", ",".join(cwPreds)]
            outFile = None
            if self.settings["saveResults"]:
                outFile = output_filename
                params += ["-r", outFile]

            # execute
            params = map(str, params)
            print "\nStarting J-MLNs..."
            print "\ncommand:\n%s\n" % " ".join(params)
            t_start = time.time()
            call(params)
            t_taken = time.time() - t_start

            if outFile is not None:
                results = dict(readAlchemyResults(outFile))

        else:  # engine is Alchemy
            haveOutFile = True
            infile = mlnFiles[0]
            mlnObject = None
            # explicitly convert MLN to Alchemy format, i.e. resolve weights that are arithm. expressions (on request) -> create temporary file
            if self.settings["convertAlchemy"]:
                print "\n--- temporary MLN ---\n"
                mlnObject = MLN.MLN(input_files)
                infile = input_files[0]
                infile = infile[:infile.rfind(".")] + ".alchemy.mln"
                f = file(infile, "w")
                mlnObject.write(f)
                f.close()
                mlnObject.write(sys.stdout)
                input_files = [infile]
                print "\n---"
            # get alchemy version-specific data
            alchemy_version = self.alchemy_versions[engine]
            if type(alchemy_version) != dict:
                alchemy_version = {"path": str(alchemy_version)}
            usage = config1.default_infer_usage
            if "usage" in alchemy_version:
                usage = alchemy_version["usage"]
            # find alchemy binary
            path = alchemy_version["path"]
            path2 = os.path.join(path, "bin")
            if os.path.exists(path2):
                path = path2
            alchemyInfer = os.path.join(path, "infer")
            if not os.path.exists(alchemyInfer) and not os.path.exists(alchemyInfer + ".exe"):
                error = "Alchemy's infer/infer.exe binary not found in %s. Please configure Alchemy in python/configMLN.py" % path
                tkMessageBox.showwarning("Error", error)
                raise Exception(error)
            # parse additional parameters for input files
            add_params = shlex.split(params)
            i = 0
            while i < len(add_params):
                if add_params[i] == "-i":
                    input_files.append(add_params[i + 1])
                    del add_params[i]
                    del add_params[i]
                    continue
                i += 1
            # create command to execute
            if output_filename is None: raise Exception("For Alchemy, provide an output filename!")
            params = [alchemyInfer, "-i", ",".join(input_files), "-e", db, "-q", query, "-r", output_filename,
                      self.alchemy_methods[method]] + add_params
            if self.settings["numChains"] != "":
                params += [usage["numChains"], self.settings["numChains"]]
            if self.settings["maxSteps"] != "":
                params += [usage["maxSteps"], self.settings["maxSteps"]]
            owPreds = []
            if self.settings["openWorld"]:
                print "\nFinding predicate names..."
                preds = MLN.getPredicateList(infile)
                owPreds = filter(lambda x: x not in cwPreds, preds)
                params += [usage["openWorld"], ",".join(owPreds)]
            if len(cwPreds) > 0:
                params += ["-cw", ",".join(cwPreds)]
            # remove old output file (if any)
            if os.path.exists(output_filename):
                os.remove(output_filename)
                pass
            # execute
            params = map(str, params)
            print "\nStarting Alchemy..."
            command = subprocess.list2cmdline(params)
            print "\ncommand:\n%s\n" % " ".join(params)
            t_start = time.time()
            call(params)
            t_taken = time.time() - t_start
            # print results file
            if True:
                print "\n\n--- output ---\n"
                results = dict(readAlchemyResults(output_filename))
                for atom, prob in results.iteritems():
                    print "%.4f  %s" % (prob, atom)
                print "\n"
            # append information on query and mln to results file
            f = file(output_filename, "a")
            dbfile = file(db, "r")
            db_text = dbfile.read()
            dbfile.close()
            infile = file(infile, "r")
            mln_text = infile.read()
            infile.close()
            f.write(
                "\n\n/*\n\n--- command ---\n%s\n\n--- evidence ---\n%s\n\n--- mln ---\n%s\ntime taken: %fs\n\n*/" % (
                command, db_text.strip(), mln_text.strip(), t_taken))
            f.close()
            # delete temporary mln
            if self.settings["convertAlchemy"] and not config_value("keep_alchemy_conversions", True):
                os.unlink(infile)

        # open output file in editor
        if False and haveOutFile and config1.query_edit_outfile_when_done:  # this is mostly useless
            editor = config1.editor
            params = [editor, output_filename]
            print 'starting editor: %s' % subprocess.list2cmdline(params)
            subprocess.Popen(params, shell=False)

        return results


class MLNLearn:
    def __init__(self):
        self.pymlns_methods = MLN.ParameterLearningMeasures.getNames()
        self.alchemy_methods = {
            "pseudo-log-likelihood via BFGS": (["-g"], False, "pll"),
            "sampling-based log-likelihood via diagonal Newton": (["-d", "-dNewton"], True, "slldn"),
            "sampling-based log-likelihood via rescaled conjugate gradient": (["-d", "-dCG"], True, "sllcg"),
            "[discriminative] sampling-based log-likelihood via diagonal Newton": (["-d", "-dNewton"], False, "dslldn"),
            "[discriminative] sampling-based log-likelihood via rescaled conjugate gradient": (
            ["-d", "-dCG"], False, "dsllcg"),
        }
        # self.alchemy_versions = config.alchemy_versions

    def run(self, **kwargs):
        '''
            required arguments:
                training databases(s): either one of
                    "dbs": list of database filenames (or MLN.Database objects for PyMLNs)
                    "db": database filename
                    "pattern": file mask pattern from which to generate the list of databases
                "mln": an MLN filename (or MLN.MLN object for PyMLNs)
                "method": the learning method name
                "output_filename": the output filename

            optional arguments:
                "engine": either "PyMLNs" (default) or one of the Alchemy versions defined in the config
                "initialWts": (true/false)
                "usePrior": (true/false); default: False
                "priorStdDev": (float) standard deviation of prior when usePrior=True
                "addUnitClauses": (true/false) whether to add unit clauses (Alchemy only); default: False
                "params": (string) additional parameters to pass to the learner; for Alchemy: command-line parameters; for PyMLNs: either dictionary string (e.g. "foo=bar, baz=2") or a dictionary object
                ...
        '''
        defaults = {
            "engine": "PyMLNs",
            "usePrior": False,
            "priorStdDev": 10.0,
            "addUnitClauses": False,
            "params": ""
        }
        self.settings = defaults
        self.settings.update(kwargs)

        # determine training databases(s)
        if "dbs" in self.settings:
            dbs = self.settings["dbs"]
        elif "db" in self.settings and self.settings["db"] != "":
            dbs = [self.settings["db"]]
        elif "pattern" in self.settings and self.settings["pattern"] != "":
            dbs = []
            pattern = settings["pattern"]
            dir, mask = os.path.split(os.path.abspath(pattern))
            for fname in os.listdir(dir):
                if fnmatch(fname, mask):
                    dbs.append(os.path.join(dir, fname))
            if len(dbs) == 0:
                raise Exception("The pattern '%s' matches no files" % pattern)
            print "training databases:", ",".join(dbs)
        else:
            raise Exception(
                "No training data given; A training database must be selected or a pattern must be specified")

            # check if other required arguments are set
        missingSettings = set(["mln", "method", "output_filename"]).difference(set(self.settings.keys()))
        if len(missingSettings) > 0:
            raise Exception("Some required settings are missing: %s" % str(missingSettings))

        params = self.settings["params"]
        method = self.settings["method"]
        discriminative = "discriminative" in method

        if self.settings["engine"] in ("PyMLNs", "internal"):  # PyMLNs internal engine
            # arguments
            args = {"initialWts": False}
            if type(params) == str:
                params = eval("dict(%s)" % params)
            elif type(params) != dict:
                raise ("Argument 'params' must be string or a dictionary")
            args.update(params)  # add additional parameters
            if discriminative:
                args["queryPreds"] = self.settings["nePreds"].split(",")
            if self.settings["usePrior"]:
                args["gaussianPriorSigma"] = float(self.settings["priorStdDev"])
            # learn weights
            if type(self.settings["mln"]) == str:
                mln = MLN.MLN(self.settings["mln"])
            elif type(self.settings["mln"] == MLN.MLN):
                mln = self.settings["mln"]
            else:
                raise Exception("Argument 'mln' must be either string or MLN object")
            mln.learnWeights(dbs, method=MLN.ParameterLearningMeasures.byName(method), **args)
            # determine output filename
            fname = self.settings["output_filename"]
            mln.write(file(fname, "w"))
            print "\nWROTE %s\n\n" % fname
            # mln.write(sys.stdout)
        else:  # Alchemy
            if self.settings["engine"] not in self.alchemy_versions:
                raise Exception("Invalid alchemy version '%s'. Known versions: %s" % (
                self.settings["engine"], ", ".join(lambda x: '"%s"' % x, self.alchemy_versions.keys())))
            alchemy_version = self.alchemy_versions[self.settings["engine"]]
            if type(alchemy_version) != dict:
                alchemy_version = {"path": str(alchemy_version)}
            # find binary
            path = alchemy_version["path"]
            path2 = os.path.join(path, "bin")
            if os.path.exists(path2):
                path = path2
            alchemyLearn = os.path.join(path, "learnwts")
            if not os.path.exists(alchemyLearn) and not os.path.exists(alchemyLearn + ".exe"):
                error = "Alchemy's learnwts/learnwts.exe binary not found in %s. Please configure Alchemy in python/configMLN.py" % path
                tkMessageBox.showwarning("Error", error)
                raise Exception(error)
            # run Alchemy's learnwts
            method_switches, discriminativeAsGenerative, shortname = self.alchemy_methods[method]
            params = [alchemyLearn] + method_switches + ["-i", self.settings["mln"], "-o",
                                                         self.settings["output_filename"], "-t",
                                                         ",".join(dbs)] + shlex.split(params)
            if discriminative:
                params += ["-ne", self.settings["nePreds"]]
            elif discriminativeAsGenerative:
                preds = MLN.getPredicateList(self.settings["mln"])
                params += ["-ne", ",".join(preds)]
            if not self.settings["addUnitClauses"]:
                params.append("-noAddUnitClauses")
            if not self.settings["usePrior"]:
                params.append("-noPrior")
            else:
                if self.settings["priorStdDev"] != "":
                    params += ["-priorStdDev", self.settings["priorStdDev"]]

            command = subprocess.list2cmdline(params)
            print "\n", command, "\n"

            # print "running Alchemy's learnwts..."
            p = subprocess.Popen(params, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            cin, cout = p.stdin, p.stdout
            # cin, cout = os.popen2(command)
            output_text = ""
            while True:
                l = cout.readline()
                if l == "":
                    break
                print l,
                output_text += l

            # add data reported by learnwts and, from the input mln, domain declarations and rules for mutual exclusiveness and exhaustiveness
            if True:
                # read the input file
                f = file(self.settings["mln"], "r")
                text = f.read()
                f.close()
                comment = re.compile(r'//.*?^|/\*.*\*/', re.DOTALL | re.MULTILINE)
                text = re.sub(comment, '', text)
                merules = []
                domain_decls = []
                for l in text.split("\n"):
                    l = l.strip()
                    # domain decls
                    if "{" in l:
                        domain_decls.append(l)
                    # mutex rules
                    m = re.match(r"\w+\((.*?)\)", l)
                    if m != None and m.group(0) == l and ("!" in m.group(1)):
                        merules.append(m.group(0))
                # read the output file
                f = file(self.settings["output_filename"], "r")
                outfile = f.read()
                f.close()
                # rewrite the output file
                f = file(self.settings["output_filename"], "w")
                # - get report with command line and learnwts output
                if config.learnwts_full_report:
                    report = output_text
                else:
                    report = output_text[output_text.rfind("Computing counts took"):]
                report = "/*\n%s\n\n%s*/\n" % (command, report)
                # - write
                outfile = outfile.replace("//function declarations", "\n".join(merules))
                if not config.learnwts_report_bottom: f.write(report + "\n")
                f.write("// domain declarations\n" + "\n".join(domain_decls) + "\n\n")
                f.write(outfile)
                if config.learnwts_report_bottom: f.write("\n\n" + report)
                f.close()


Large_Font=("Verdana",12)
class App(tk.Tk):
    def __init__(self,*args,**kwargs):
        tk.Tk.__init__(self,*args,**kwargs)
        container = tk.Frame(self)
        container.pack(side="top", fill="both",expand = True)
        container.grid_rowconfigure(0,weight=1)
        # container.grid_columnconfigure(0,weight=1)
        self.frames = {}
        for F in (StartPage,PageOne, PageTwo):

            self.title('IFT Tool Box')

            frame= F(container,self) # pass the container and self into the StartPage, not sure about the self.container?

            self.frames[F] =frame

            frame.grid(row=0, column=0, stick="nsew")

        self.show_frame(StartPage)

    def show_frame(self,cont):
        frame = self.frames[cont]
        if cont==PageOne:
            self.geometry("570x550")
        elif cont==StartPage:
            tmp =1
            # self.geometry("1200x760")
        elif cont==PageTwo:
            self.geometry("570x550")

        print self.winfo_width()
        print self.winfo_height()
        frame.tkraise()
        menubar = frame.menubar_1(self)
        self.config(menu = menubar)

class StartPage(tk.Frame):
    def __init__(self,parent, controller):
        tk.Frame.__init__(self,parent)
        self.pack(fill=BOTH, expand=1)
        self.rowconfigure(1,weight =1)
        self.columnconfigure(0,weight=1)
        # self.columnconfigure(1, weight=1)
        # self.columnconfigure(2, weight=1)
        # self.columnconfigure(3, weight=1)
        # self.columnconfigure(0,weight = 1)
        # self.pack(fill=BOTH, expand=1)
        self.default_settings = {"numChains": "1", "maxSteps": "", "saveResults": False, "convertAlchemy": False,
                                 "openWorld": True}

        print(self.default_settings)
        self.settings = dict(self.default_settings)
        self.numEngine=1
        if not "queryByDB" in self.settings: self.settings["queryByDB"] = {}
        if not "emlnByDB" in self.settings: self.settings["emlnByDB"] = {}

        self.grid(row=0, column=3, sticky='NEWS')
        helv36 = tkFont.Font(family='Helvetica', size=32, weight=tkFont.BOLD)
        var = IntVar()

        row = 0

        lab2=Label(self,text='Decision Rule:')
        lab2.grid(row=row, column=0,sticky=W)
        lab3=Label(self,text='Evidence:')
        lab3.grid(row=row, column = 2,sticky=W)
        btn_edit = Button(self,text="Edit",command=lambda :controller.show_frame(PageOne))
        btn_edit.grid(row= row, column=1,sticky= E)
        btn_edit_evi = Button(self,text="Edit",command= lambda: controller.show_frame(PageTwo))
        btn_edit_evi.grid(row = row, column=3, sticky=E)
        row +=1

        self.text_load = ScrolledText(self, background='bisque')
        self.text_load.grid(row = row, column = 0, columnspan = 2,sticky='NEWS')
        self.text_load.insert(INSERT,'Rule description...')

        self.text_res= ScrolledText(self, background='bisque')
        self.text_res.insert(INSERT,'Evidence Database...')
        self.text_res.grid(row=row,column=2,columnspan=2,sticky="NEWS")
        row +=1


        row +=2


        LabelQuerry = Label(self,text = 'Querry:')
        LabelQuerry.grid(row= row, column = 0, sticky = 'W')
        row +=1
        self.query = StringVar()
        self.query.set(self.settings.get("query", "smokes"))
        Entry(self, textvariable=self.query).grid(row=row, column=0, columnspan = 2, sticky="NEW")
        row +=1


        row +=1
        Label(self,text="Engine:").grid(row = row, column = 0, sticky="W")
        Label(self,text="Method:").grid(row = row, column = 1, sticky="W")
        Label(self,text="Iteration:").grid(row = row, column = 2, sticky = "W")
        Label(self,text="Learning Configuration:").grid(row = row, column = 3, sticky = "W")
        row +=1
        self.res_eig = StringVar()
        self.res_eig.set('PyMLNs')
        # option =OptionMenu(self,self.res_eig,"PyMLNs","J-MLNs")
        option = OptionMenu(self, self.res_eig, "PyMLNs")
        option.grid(row  = row, column=0, sticky='WE')
        # yscroll = Scrollbar(self, orient=VERTICAL)
        # yscroll.grid(row  = row, column=1,  padx=(0,280), sticky='NSW')
        # statesList = ["MLN", "BLN"]
        # conOFlstNE = StringVar()
        # lstNE = Listbox(self, listvariable=conOFlstNE, yscrollcommand=yscroll.set)
        # lstNE.grid(row=row, column=0, rowspan = 1,columnspan= 1, sticky='WENS')
        # conOFlstNE.set(tuple(statesList))
        # yscroll["command"] = lstNE.yview
        # lstNE.bind("<Double-Button-1>", self.OnDouble)
        #
        self.opt_method = StringVar()
        self.opt_method.set('Gibbs sampling')
        # option2 =OptionMenu(self,self.opt_method,"MC-SAT", "Gibbs sampling","Exact Inference")
        option2 =OptionMenu(self,self.opt_method, "Gibbs sampling")

        option2.grid(row  = row, column=1, sticky='WE')

        self.itr = StringVar()
        self.itr.set('500')
        option3 = OptionMenu(self, self.itr, "500", "1000", "5000","10000")
        option3.grid(row=row, column=2, sticky='WE')


        self.lea_con = StringVar()
        self.lea_con.set('pseudo-log-likelihood')
        # option4 = OptionMenu(self, self.lea_con, "pseudo-log-likelihood", "log-likelihood","Diagonal Newton","Sampling based log-likelihood")
        option4 = OptionMenu(self, self.lea_con, "pseudo-log-likelihood", "log-likelihood")

        option4.grid(row=row, column=3, sticky='WE')


        row += 4
        btn2=Button(self,text="Inference",command=self.start)
        btn2.grid(row=row,column =0,sticky=W)
        btn3=Button(self, text="Learn", command = self.learn)
        btn3.grid(row=row,column =3, sticky = E)
        # btn4 = Button(self, text="Learn", command=self.start)
        # btn4.grid(row = row, column=1,sticky = E+W)

        row +=1

        self.text1 = ScrolledText(self, background="green",height =5)
        self.text1.grid(row = row, column = 0, rowspan=2, columnspan = 4,sticky='EW')
        self.text1.insert(INSERT,'Running...'+'\n')


        checkbutton = Checkbutton(self, text='Save Log File', variable=var, command=lambda :controller.show_frame(PageOne))
        checkbutton.grid(columnspan=2, sticky=W)


    def OnDouble(self, event):
        widget = event.widget
        selection=widget.curselection()
        value = widget.get(selection[0])
        print "selection:", selection, ": '%s'" % value
### Menu bar set up:
    def menubar_1(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Load MLN file",command=self.Open_File)
        filemenu.add_command(label="Laod Evidence file", command = self.Open_File_Evidence)
        # filemenu.add_command(label="Load Configuration file")

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo")
        editmenu.add_separator()
        editmenu.add_command(label="Cut")

        menubar.add_cascade(label="Edit")
        optionmenu = Menu(menubar, tearoff=0)
        submenu = Menu(optionmenu)
        submenu.add_command(label="MLN")
        submenu.add_command(label='BLN')
        optionmenu.add_cascade(label="Model Selection", menu=submenu)
        optionmenu.add_command(label="Data-Driven")
        optionmenu.add_command(label="Model-Driven")
        menubar.add_cascade(label="Option", menu=optionmenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help instruction")
        return  menubar
    def Open_File(self):
        self.mln_filename = tkFileDialog.askopenfilename(initialdir=".", title="Select file", filetypes=(
            ("mln files", "*.mln"), ("all files", "*.*")))
        print(self.mln_filename)
        f = open(self.mln_filename)
        print f

        self.text_load.delete('1.0', END)
        self.text_load.insert(1.0,'File Path:'+ self.mln_filename+'\n')
        self.text_load.insert(END, '//==========================================================' + '\n')
        self.text_load.insert(END, f.read())
        # self.text1.delete('1.0', END)
        self.text1.insert(END, self.mln_filename)
    def Open_File_Evidence(self):
        self.db_filename = tkFileDialog.askopenfilename(initialdir=".", title="Select file", filetypes=(
            ("db files", "*.db"), ("all files", "*.*")))
        f = open(self.db_filename)
        self.text_res.configure(state='normal')
        self.text_res.delete('1.0',END)
        self.text_res.insert(1.0,'File Path:' + self.db_filename+'\n')
        self.text_res.insert(END, '//==========================================================' + '\n')
        self.text_res.insert(END, f.read())
        self.text_res.configure(state='disabled')
        # self.text1.delete('1.0', END)
        self.text1.insert(END, self.db_filename)
    def start(self):
        mln=self.mln_filename
        emln = ''
        db =self.db_filename
        qf =''
        mln_text=self.text_load.get(1.0,END)
        db_text=self.text_res.get(1.0,END)
        qf_text=u'\n'
        output='two-smokers.results'
        method =self.opt_method.get()
        params = 'debug=False'
        method2 = self.opt_method.get()
        self.selected_engine = StringVar()
        self.selected_engine.set(self.res_eig.get())
        # self.query= StringVar()
        # update settings
        self.settings["mln"] = mln
        # self.settings["mln_rename"] = self.selected_mln.rename_on_edit.get()
        self.settings["db"] = db
        # self.settings["db_rename"] = self.selected_db.rename_on_edit.get()
        self.settings["method%d" % int(self.numEngine)] = self.opt_method.get()
        self.settings["params%d" % int(self.numEngine)] = params
        self.settings["query"] = self.query.get()
        # self.settings["query"]="friends,cancer"
        print(self.settings["query"])
        self.settings["queryByDB"][db] = self.settings["query"]
        self.settings["emlnByDB"][db] = emln
        self.settings["engine"] = self.selected_engine.get()
        self.settings["qf"] = qf
        self.settings["output_filename"] = output
        self.open_world = IntVar()
        self.settings["openWorld"] = self.open_world.get()

        self.cwPreds = StringVar()
        self.settings["cwPreds"] = self.cwPreds.get()

        # self.cwPreds = StringVar()
        # self.cwPreds.set(self.settings.get("cwPreds", ""))
        #
        # self.open_world.set(self.settings.get("openWorld", True))

        self.convert_to_alchemy = IntVar()
        self.convert_to_alchemy.set(self.settings.get("convertAlchemy", 0))
        self.settings["convertAlchemy"] = self.convert_to_alchemy.get()

        self.use_emln = IntVar()
        self.use_emln.set(self.settings.get("useEMLN", 0))
        self.settings["useEMLN"] = self.use_emln.get()

        self.maxSteps = StringVar()
        self.maxSteps.set(self.settings.get("maxSteps", "10000"))
        self.settings["maxSteps"] = self.itr.get()

        self.numChains = StringVar()
        self.settings["numChains"] = self.numChains.get()
        if "params" in self.settings: del self.settings["params"]
        # if saveGeometry:
        #     self.settings["geometry"] = self.master.winfo_geometry()
        # self.settings["saveResults"] = self.save_results.get()
        # write query to file
        write_query_file = False
        if write_query_file:
            query_file = "%s.query" % db
            f = file(query_file, "w")
            f.write(self.settings["query"])
            f.close()
        # write settings
        # pickle.dump(self.settings, file(configname, "w+"))
        # some information
        print "\n--- query ---\n%s" % self.settings["query"]
        print "\n--- evidence (%s) ---\n%s" % (db, db_text.strip())
        # MLN input files
        input_files = [mln]
        # if settings["useEMLN"] == 1 and emln != "": # using extended model
        #     input_files.append(emln)
        # # hide main window
        # self.master.withdraw()
        # runinference
        self.inference = MLNInfer()
        self.results = self.inference.run(input_files, db, method, self.settings["query"], params=params, **self.settings)
        self.text1.insert(END, u'\n')
        for key in self.results:
            self.text1.insert(END,self.results[key])
            self.text1.insert(END,':'+'\t')
            self.text1.insert(END, key)
            self.text1.insert(END,u'\n')


        # self.text1.insert(1,self.results)
        # self.inference.run(input_files, db, method, self.settings["query"], params=params, **self.settings)

        # restore main window

        # self.master.deiconify()
        # self.setGeometry()
        # # reload the files (in case they changed)
        # self.selected_mln.reloadFile()
        # self.selected_db.reloadFile()

        sys.stdout.flush()


    def learn(self, saveGeometry=True):
        # try:
            # update settings
            # mln = self.selected_mln.get()
            mln = self.mln_filename
            db =self.db_filename

            # db = self.selected_db.get()
            if mln == "":
                raise Exception("No MLN was selected")
            # method = self.selected_method.get()
            method= self.lea_con.get()
            # params = self.params.get()
            params =''
            self.settings["mln"] = mln
            self.settings["db"] = db
            # self.settings["output_filename"] = self.output_filename.get()
            self.settings["output_filename"]='res.mln'
            self.internalMode =True
            self.settings["params%d" % int(self.internalMode)] = params
            # self.settings["engine"] = self.selected_engine.get()
            self.settings["engine"]="internal"
            self.settings["method%d" % int(self.internalMode)] = method
            # self.settings["pattern"] = self.entry_pattern.get()
            self.settings["pattern"] = ""
            # self.settings["usePrior"] = int(self.use_prior.get())
            self.settings["usePrior"]=0
            # self.settings["priorStdDev"] = self.priorStdDev.get()
            self.settings["priorStdDev"] =100
            # self.settings["nePreds"] = self.nePreds.get()
            self.settings["nePreds"]=""
            # self.settings["addUnitClauses"] = int(self.add_unit_clauses.get())
            self.settings["addUnitClauses"]=0
            if saveGeometry:
                self.settings["geometry"] = self.master.winfo_geometry()
            pickle.dump(self.settings, file("learnweights.config.dat", "w+"))

            # hide gui
            # self.master.withdraw()

            # invoke learner

            self.learner = MLNLearn()
            self.learner.run(params=params, method=method, **self.settings)
            self.mln_filename=self.settings["output_filename"]

            f = open(self.mln_filename)
            self.text_load.delete('1.0', END)
            self.text_load.insert(1.0,'File Path:'+ self.mln_filename+'\n')
            self.text_load.insert(END,'//=========================================================='+'\n')
            self.text_load.insert(END, f.read())
            # self.text1.delete('1.0', END)
            self.text1.insert(END, 'The rule with learnt weights is saved in the file:')
            self.text1.insert(END, self.mln_filename+'\n')
            sys.stdout.flush()



            # if config.learnwts_edit_outfile_when_done:
            #     params = [config.editor, self.settings["output_filename"]]
            #     print "starting editor: %s" % subprocess.list2cmdline(params)
            #     subprocess.Popen(params, shell=False)
        # except:
        #     cls, e, tb = sys.exc_info()
        #     sys.stderr.write("%s: %s\n" % (str(type(e)), str(e)))
        #     traceback.print_tb(tb)
        #     raise
        # finally:
        #     # restore gui
        #     self.master.deiconify()
        #     self.setGeometry()
        #
        #     sys.stdout.flush()


class PageOne(tk.Frame):
    def __init__(self,parent, controller):

        tk.Frame.__init__(self,parent)
        self.rowconfigure(0,weight =1)
        self.columnconfigure(0,weight = 1)
        self.grid(row=0, column=2, sticky='NEWS')
        helv36 = tkFont.Font(family='Helvetica', size=20, weight=tkFont.BOLD)
        var = IntVar()

        row = 0
        lab1 = Label(self, text="MLN Rules Editor", font=helv36)

        lab1.grid(row=row, column=0, columnspan=1, sticky='WENS')


        row +=1
        lab2=Label(self,text='Decision Rule:')
        lab2.grid(row=row, column=0,sticky='NW')
        row +=1
        self.text_load= Text(self)
        self.text_load.insert(INSERT,'Rule description...')
        self.text_load.grid(row=row,column=0, rowspan=1,columnspan=2,sticky="WE")


        row +=1
        btn2=Button(self,text="Main Menu",command=lambda: controller.show_frame(StartPage))
        btn2.grid(row=row,sticky=W)
        btn3=Button(self, text="Save",command=self.Save_File)
        btn3.grid(row=row,column =1, sticky = "E")

        row +=1
        # This part is for display text file.
        self.text1 = Text(self,background="green", foreground="black",height=5)
        self.text1.insert(INSERT,'Running...')
        self.text1.grid(row=row,column=0, rowspan=2, columnspan =2, sticky='EW' )
        # yscrollbar=Scrollbar(frame, orient=VERTICAL, command=text1.yview)
        checkbutton = Checkbutton(self, text='Save Log File', variable=var)
        checkbutton.grid(columnspan=2, sticky=W)

    def menubar_1(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Open", command=self.Open_File)
        filemenu.add_command(label="Save", command=self.Save_File)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        return menubar

    def Open_File(self):
        self.filename = tkFileDialog.askopenfilename(initialdir=".", title="Select file", filetypes=(
            ("db files", "*.mln"), ("all files", "*.*")))
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,self.filename)
        self.text1.configure(state='disabled')
        f = open(self.filename)
        print f
        self.text_load.delete('1.0', END)
        self.text_load.insert(1.0, f.read())

    def Save_File(self):
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".mln")
        if f is None:
            return
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,f.name)
        self.text1.configure(state='disabled')
        text2save = str(self.text_load.get(1.0, END))  # starts from `1.0`, not `0.0`
        f.write(text2save)
        f.close()


class PageTwo(tk.Frame):
    def __init__(self,parent, controller):

        tk.Frame.__init__(self,parent)
        self.rowconfigure(0,weight =1)
        self.columnconfigure(0,weight = 1)
        self.grid(row=0, column=2, sticky='NEWS')
        helv36 = tkFont.Font(family='Helvetica', size=20, weight=tkFont.BOLD)
        var = IntVar()

        row = 0
        lab1 = Label(self, text="MLN Evidence Editor", font=helv36)
        lab1.grid(row=row, column=0, columnspan=2, sticky='N')

        row +=1
        lab2=Label(self,text='Decision Rule:')
        lab2.grid(row=row, column=0,sticky=W)
        row +=1
        self.text_load= Text(self)
        self.text_load.insert(INSERT,'DATA description...')
        self.text_load.grid(row=row,column=0, rowspan=1,columnspan=2,sticky="W")


        row +=1
        btn2=Button(self,text="Main Menu",command=lambda: controller.show_frame(StartPage))
        btn2.grid(row=row,sticky=W)
        btn3=Button(self, text="Save",command=self.Save_File)
        btn3.grid(row=row,column =1, sticky = "E")

        row +=1
        # This part is for display text file.
        self.text1 = Text(self,background="green", foreground="black",height=5)
        self.text1.insert(INSERT,'Running...')
        self.text1.grid(row=row,column=0, rowspan=2, columnspan =2, sticky='EW' )
        # yscrollbar=Scrollbar(frame, orient=VERTICAL, command=text1.yview)
        checkbutton = Checkbutton(self, text='Save Log File', variable=var)
        checkbutton.grid(columnspan=2, sticky=W)

    def menubar_1(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Open", command=self.Open_File)
        filemenu.add_command(label="Save", command=self.Save_File)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        return menubar
    # Evidence Dataset
    def Open_File(self):
        self.filename = tkFileDialog.askopenfilename(initialdir=".", title="Select file", filetypes=(
            ("db files", "*.db"), ("all files", "*.*")))
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,self.filename)
        self.text1.configure(state='disabled')
        f = open(self.filename)
        print f
        self.text_load.delete('1.0', END)
        self.text_load.insert(1.0, f.read())

    def Save_File(self):
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".mln")
        if f is None:
            return
        self.text1.configure(state='normal')
        self.text1.delete('1.0',END)
        self.text1.insert(1.0,f.name)
        self.text1.configure(state='disabled')
        text2save = str(self.text_load.get(1.0, END))  # starts from `1.0`, not `0.0`
        f.write(text2save)
        f.close()

def main():

    app = App()

    app.mainloop()


if __name__=='__main__':
   main()



