import arcpy
import csv
import cPickle as pickle
import os
import sys

class sharedTools(object):
    METADATA_DEFAULT_NAME = "acs_metadata.p"
    def __init__(self):
        pass

    @staticmethod
    def get_script_path():
        return os.path.dirname(os.path.realpath(__file__))

    @staticmethod
    def get_pickle_data():
        nm = sharedTools.get_script_path() + "\\" + sharedTools.METADATA_DEFAULT_NAME
        return nm

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Census Tools"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [BuildMetadataList,Extractor,Combiner,Divider,RenameField,Finder]


class BuildMetadataList(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Build Metadata Field List"
        self.description = "Loads the metadata for use"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
                displayName='ACS Workspace',
                name='acs_ws',
                datatype='Workspace',
                parameterType='Required',
                direction='Input')

        param1 = arcpy.Parameter(
            displayName="Metadata Table",
            name="selectedTable",
            datatype="string",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Updates after setting workspace"]

        param2 = arcpy.Parameter(
            displayName="Field Order",
            name="fields",
            datatype="string",
            parameterType="Required",
            direction="Input")
        param2.value= "Short_Name;Full_Name"
        params = [param0,param1,param2]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        if parameters[0].valueAsText:
            if not parameters[1].altered:
                if arcpy.Exists(parameters[0].valueAsText):
                    arcpy.env.workspace = parameters[0].valueAsText
                    parameters[1].filter.list = arcpy.ListTables()

        return

    def updateMessages(self, parameters):

        return


    def execute(self, parameters, messages):
        """The source code of the tool."""
        inputWS = parameters[0].valueAsText
        inputTable = parameters[1].valueAsText
        inputFieldOrder = parameters[2].valueAsText
        fields = inputFieldOrder.split(";")
        arcpy.AddMessage(fields)
        arcpy.AddMessage(sharedTools.get_script_path())
        if len(fields)>2:
            arcpy.AddError("Too many fields")
        arcpy.env.workspace = inputWS
        with arcpy.da.SearchCursor(inputTable,fields) as sc:
            outDict = {}
            for row in sc:
                outDict[row[0]] = "{0}|{1}".format(row[0],row[1])

        pickle.dump(outDict,open(sharedTools.get_pickle_data(),'wb'))


class Finder(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find a field"
        self.description = "Searchers through the ACS tables to find a field"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Field Name",
            name="newFieldName",
            datatype="String",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
                displayName='ACS Workspace',
                name='acs_ws',
                datatype='Workspace',
                parameterType='Required',
                direction='Input')


        params = [param0,param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def matchScore(self, matchingWord,wordForMatchScore):
        matchingWord = matchingWord.lower()
        wordForMatchScore = wordForMatchScore.lower()
        matchCount = 0
        for i in range(0,len(matchingWord)):
            try:
                if matchingWord[i] == wordForMatchScore[i]:
                    matchCount+=1
            except:
                break
        return (float(matchCount)/float(len(matchingWord)))

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inputFieldName = parameters[0].valueAsText
        inputWS = parameters[1].valueAsText
        arcpy.env.workspace = inputWS
        tables = arcpy.ListTables()
        for t in tables:
            fieldNames = [f.name for f in arcpy.ListFields(t)]
            for f in fieldNames:
                if self.matchScore(inputFieldName,f) >.85:
                    arcpy.AddMessage("Close match found in table {0}, named {1}.".format(t,f))

class Extractor(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ACS Extract Fields and Values"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="ACS Geography Units (Append Values)",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
                displayName='GEOID Field',
                name='geoid_fields',
                datatype='Field',
                parameterType='Required',
                direction='Input')

        param1.parameterDependencies = [param0.name]
        param1.value = "GEOID_Data"
        param3 = arcpy.Parameter(
            displayName="ACS Data Table",
            name="in_table",
            datatype="Table",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
                displayName='GEOID Field',
                name='geoid_fieldtable',
                datatype='Field',
                parameterType='Required',
                direction='Input')
        param4.value = "GEOID"
        param4.parameterDependencies = [param3.name]

        param5 = arcpy.Parameter(
            displayName="Select ACS Fields",
            name="listvalues",
            datatype="String",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param5.filter.list =  []

        params = [param0,param1,param3,param4,param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #print "update parameters"
        #if len(parameters[4].filter.list) ==0:
            #print "filter list is zero"
            #print "param3 %s"%parameters[3].valueAsText
            #if parameters[3].valueAsText != "":


        if len(parameters[4].filter.list)==0:
            fields = arcpy.ListFields(parameters[2].valueAsText)
            zcd = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
            res = []
            for f in fields:
                try:
                    val = zcd[f.name]
                    if "Estimate" in val:
                        res.append(val)
                except:
                    pass

            parameters[4].filter.list = res
        #self.zctametadata = list(csv.reader(open(r"C:\Users\David\OneDrive\projects\learningGate\ZCTA_METADATA_2015.txt",'rb'),delimiter='\t'))
        #self.zctametadata.pop(0)
        #self.zctaselector = ["%s|%s"%(row[0],row[1]) for row in self.zctametadata]
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        #if len(parameters[4].filter.list) ==0:
            #parameters[4].filter.list = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inputFC = parameters[0].valueAsText
        inputFCField = parameters[1].valueAsText
        inputTable = parameters[2].valueAsText
        inputFieldTab = parameters[3].valueAsText

        inputNewFields = parameters[4].values

        fieldsToFind = [txt.split("|")[0] for txt in inputNewFields]
        fieldProps = []
        for x in fieldsToFind:
            found = arcpy.ListFields(inputTable,x)
            if len(found) ==1:
                fieldProps.append(found[0])

        for f in fieldProps:
            #try:
            arcpy.AddField_management(inputFC,f.name,f.type,field_precision=f.precision,field_scale=f.scale,field_length=f.length)
            #except:
                #pass
        fieldNamesOnly = [f.name for f in fieldProps]

        with arcpy.da.SearchCursor(inputFC,[inputFCField]) as sc:
            geoIDList = ["'%s'"%row[0] for row in sc]
        wc = arcpy.AddFieldDelimiters(inputTable,inputFieldTab) + " in (%s)"%(",".join(geoIDList))

        arcpy.AddMessage(wc)
        data = {}
        with arcpy.da.SearchCursor(inputTable,[inputFieldTab]+fieldNamesOnly,where_clause=wc) as sc:
            for row in sc:
                data[row[0]]={fieldNamesOnly[i]:row[i+1] for i in range(0,len(fieldNamesOnly))}

        with arcpy.da.UpdateCursor(inputFC,[inputFCField]+fieldNamesOnly) as uc:
            for row in uc:
                tempdict = data[row[0]]
                for i,nm in enumerate(fieldNamesOnly):
                    row[i+1] = tempdict[nm]
                uc.updateRow(row)


        return

class Combiner(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ACS Combine Fields"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="ACS Geography Units (Append Values)",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
                displayName='GEOID Field',
                name='geoid_fields',
                datatype='Field',
                parameterType='Required',
                direction='Input')

        param1.parameterDependencies = [param0.name]



        param5 = arcpy.Parameter(
            displayName="Select ACS Fields",
            name="listvalues",
            datatype="String",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param5.filter.list =  []

        param6 = arcpy.Parameter(
            displayName="New Field Name",
            name="newFieldName",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param6b = arcpy.Parameter(
            displayName="New Field Alias",
            name="newFieldAlias",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param7 = arcpy.Parameter(
            displayName="Drop Fields",
            name="dropFields",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input"
        )
        param7.value = True

        params = [param0,param1,param5,param6,param6b,param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #print "update parameters"
        #if len(parameters[4].filter.list) ==0:
            #print "filter list is zero"
            #print "param3 %s"%parameters[3].valueAsText
            #if parameters[3].valueAsText != "":


        if len(parameters[2].filter.list)==0:
            fields = arcpy.ListFields(parameters[0].valueAsText)
            zcd = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
            res = []
            for f in fields:
                if f.name in zcd.keys():
                    val = zcd[f.name]
                    res.append(val)
                else:
                    res.append(f.name)


            parameters[2].filter.list = res
        #self.zctametadata = list(csv.reader(open(r"C:\Users\David\OneDrive\projects\learningGate\ZCTA_METADATA_2015.txt",'rb'),delimiter='\t'))
        #self.zctametadata.pop(0)
        #self.zctaselector = ["%s|%s"%(row[0],row[1]) for row in self.zctametadata]
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        #if len(parameters[4].filter.list) ==0:
            #parameters[4].filter.list = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inputFC = parameters[0].valueAsText
        inputFCField = parameters[1].valueAsText

        inputSumFields = parameters[2].values
        newFieldName =parameters[3].valueAsText
        newFieldAlias =parameters[4].valueAsText
        dropFields = parameters[5].value

        fieldsToSum = [txt.split("|")[0] for txt in inputSumFields]
        fieldProps = []
        for x in fieldsToSum:
            found = arcpy.ListFields(inputFC,x)
            if len(found) ==1:
                fieldProps.append(found[0])

        for f in fieldProps:
            #try:
            arcpy.AddField_management(inputFC,newFieldName,f.type,field_precision=f.precision,field_scale=f.scale,
            field_length=f.length, field_alias=newFieldAlias)
            break
            #except:
                #pass
        fieldNamesOnly = [f.name for f in fieldProps]

        with arcpy.da.UpdateCursor(inputFC,[newFieldName]+fieldNamesOnly) as uc:
            for row in uc:
                templist=[]
                for i,nm in enumerate(fieldNamesOnly):
                    if row[i+1]:
                        templist.append(row[i+1])
                    else:
                        templist.append(0)
                row[0]=sum(templist)
                uc.updateRow(row)
        if dropFields:
            arcpy.DeleteField_management(inputFC,fieldNamesOnly)

        return

class Divider(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ACS Divide By"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="ACS Geography Units (Append Values)",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")



        param5 = arcpy.Parameter(
            displayName="Numerator Field",
            name="listnumer",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list =  []

        param8 = arcpy.Parameter(
            displayName="Denominator Field",
            name="listdenom",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param8.filter.type = "ValueList"
        param8.filter.list =  []

        param9 = arcpy.Parameter(
            displayName="Multiplier",
            name="MultiplierValue",
            datatype="Double",
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="New Field Name",
            name="newFieldName",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param6b = arcpy.Parameter(
            displayName="New Field Alias",
            name="newFieldAlias",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param7 = arcpy.Parameter(
            displayName="Drop Fields",
            name="dropFields",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input"
        )
        param7.value = False

        params = [param0,param5,param8, param9,param6,param6b, param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #print "update parameters"
        #if len(parameters[4].filter.list) ==0:
            #print "filter list is zero"
            #print "param3 %s"%parameters[3].valueAsText
            #if parameters[3].valueAsText != "":


        if len(parameters[1].filter.list)==0:
            fields = arcpy.ListFields(parameters[0].valueAsText)
            zcd = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
            res = []
            for f in fields:
                if f.name in zcd.keys():
                    val = zcd[f.name]
                    res.append(val)
                else:
                    res.append(f.name)


            parameters[1].filter.list = res
            parameters[2].filter.list = res
        #self.zctametadata = list(csv.reader(open(r"C:\Users\David\OneDrive\projects\learningGate\ZCTA_METADATA_2015.txt",'rb'),delimiter='\t'))
        #self.zctametadata.pop(0)
        #self.zctaselector = ["%s|%s"%(row[0],row[1]) for row in self.zctametadata]
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        #if len(parameters[4].filter.list) ==0:
            #parameters[4].filter.list = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inputFC = parameters[0].valueAsText


        numerField = parameters[1].valueAsText
        arcpy.AddMessage(numerField)
        denomField = parameters[2].valueAsText
        arcpy.AddMessage(denomField)
        multiplier = parameters[3].value
        newFieldName =parameters[4].valueAsText
        newFieldAlias =parameters[5].valueAsText
        dropFields = parameters[6].value

        fieldsToSum = [numerField.split("|")[0],denomField.split("|")[0]]
        fieldProps = []
        for x in fieldsToSum:
            found = arcpy.ListFields(inputFC,x)
            if len(found) ==1:
                fieldProps.append(found[0])
        try:
            arcpy.AddField_management(inputFC,newFieldName,"DOUBLE",field_precision=6,field_scale=3,field_alias=newFieldAlias)
        except:
            pass
        fieldNamesOnly = [f.name for f in fieldProps]
        arcpy.AddMessage(fieldNamesOnly)
        with arcpy.da.UpdateCursor(inputFC,[newFieldName]+fieldNamesOnly) as uc:
            for row in uc:
                if row[2] != 0:
                    row[0]=float(row[1])/row[2] * multiplier
                    uc.updateRow(row)
        if dropFields:
            pass
            #arcpy.DeleteField_management(inputFC,fieldNamesOnly)

        return
        
        
class RenameField(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Rename Field"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="ACS Geography Units (Append Values)",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")



        param5 = arcpy.Parameter(
            displayName="Rename Field",
            name="listnumer",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list =  []


        param6 = arcpy.Parameter(
            displayName="New Field Name",
            name="newFieldName",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param6b = arcpy.Parameter(
            displayName="New Field Alias",
            name="newFieldAlias",
            datatype="String",
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Drop Fields",
            name="dropFields",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input"
        )
        param7.value = False

        params = [param0,param5,param6,param6b,param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #print "update parameters"
        #if len(parameters[4].filter.list) ==0:
            #print "filter list is zero"
            #print "param3 %s"%parameters[3].valueAsText
            #if parameters[3].valueAsText != "":


        if len(parameters[1].filter.list)==0:
            fields = arcpy.ListFields(parameters[0].valueAsText)
            zcd = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
            res = []
            for f in fields:
                if f.name in zcd.keys():
                    val = zcd[f.name]
                    res.append(val)
                else:
                    res.append(f.name)


            parameters[1].filter.list = res

        #self.zctametadata = list(csv.reader(open(r"C:\Users\David\OneDrive\projects\learningGate\ZCTA_METADATA_2015.txt",'rb'),delimiter='\t'))
        #self.zctametadata.pop(0)
        #self.zctaselector = ["%s|%s"%(row[0],row[1]) for row in self.zctametadata]
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        #if len(parameters[4].filter.list) ==0:
            #parameters[4].filter.list = pickle.load(open(sharedTools.get_pickle_data(),'rb'))
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        inputFC = parameters[0].valueAsText
        baseField = parameters[1].valueAsText
        newFieldName =parameters[2].valueAsText
        newFieldAlias =parameters[3].valueAsText
        dropFields = parameters[4].value

        fieldsToSum = [baseField.split("|")[0]]
        fieldProps = []
        for x in fieldsToSum:
            found = arcpy.ListFields(inputFC,x)
            if len(found) ==1:
                fieldProps.append(found[0])

        fieldProps = fieldProps[0]
        fieldNamesOnly = [fieldProps.name]
        arcpy.AddMessage(fieldNamesOnly)
        
        try:
            arcpy.AddField_management(inputFC,newFieldName,fieldProps.type,field_precision=fieldProps.precision,
            field_scale=fieldProps.scale,field_alias=newFieldAlias)
        except:
            pass
        with arcpy.da.UpdateCursor(inputFC,[newFieldName]+fieldNamesOnly) as uc:
            for row in uc:
                row[0] = row[1]
                uc.updateRow(row)
        if dropFields:
            pass
            #arcpy.DeleteField_management(inputFC,fieldNamesOnly)

        return