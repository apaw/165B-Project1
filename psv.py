from pyparsing import *

# Declare string constants and different instances of grammar
# The first is extracting the table names and attributes from CREATE TABLE statements,
# including being able to differentiate PKs
# The second is dealing with ALTER TABLE, which we'll assume is just adding FKs
# We can ignore the two views (CREATE VIEWs)
#
# Because of pyparsing, we are very specific about the formatting of the lines.

# First open up the sql file we'd like to read
sql_file = open("mondial-schema.sql")

# Define some relevant strings for parsing

open_para = "("
pk = "PRIMARY KEY"
fk = "FOREIGN KEY"
key = oneOf("PRIMARY FOREIGN _FKey", caseless = True)
identifiers = oneOf(" NOT NULL UNIQUE", caseless = True)
default = "DEFAULT " + restOfLine
sql_keyword = oneOf("ADD REFERENCES CHECK SELECT UNION AND FROM CONSTRAINT CREATE ALTER", caseless = True)

#flag for subgraph parsing

first_subgraph = 1

# Define the relevant terms needed to parse table names
# from create/alter statements

create_or_alter = oneOf("CREATE ALTER", caseless = True)
table_grammar =  create_or_alter + "TABLE " + Word( alphas + "_")

# Grammar for attribute lines

# Dealing with constraint arguments
constraints = Optional( "ADD" ) + "CONSTRAINT" + Word( alphas ) + key + Optional( key ) + "KEY" + Optional( "(" + Word(alphanums) + ZeroOrMore("," + Word(alphanums)) + ")") + restOfLine

# Dealing with type declaration
types = oneOf("VARCHAR( NUMERIC", caseless = True)
type_grammar = types + Optional( Word( nums ) ) + Optional( ")" ) + Optional( OneOrMore(identifiers) ) + Optional(default)

# Dealing with parsing lines for the actual attribute names
grammar = Optional( open_para ) + Word( alphanums ) + type_grammar + Optional( constraints )

# Dealing with reference declarations
reference_grammar = "REFERENCES" + Word ( alphanums ) + restOfLine

# And check statements
check_grammar = "CHECK" + restOfLine

buffer = ""
table_name = ""
current_attr = ""

#formatting
table_format = "node [shape=\"box3d\" style=\"filled\" color=\"#0000FF\" fillcolor=\"#EEEEEE\" fontname=\"Courier\" ]"
attr_format = "node [shape=\"box\" style=\"rounded\" width=0 height=0 color=\"#00AA00\"]"

edge_format = "edge [color=\"#00AA00\" dir=none style=\"\" label=\"\"]"
key_format = "edge [color=red dir=forward style=dashed label=\" FK\" fontname=\"Veranda\" fontcolor=red fontsize=10]"

# DOT arrows
directed = " -> "
underscore = "_"

#global variables
reference_attr = []

print "digraph mondial {"
print "rankdir=BT"
print edge_format

for line in sql_file:

	buffer += line
	match = next(table_grammar.scanString(buffer), None)

	while match: # we have encountered a CREATE TABLE or ALTER TABLE statement
		tokens, start, end = match
		table_name = tokens[-1] # get table name

		if (tokens[0] == "CREATE"): # only print the table node once, upon creation
			if(first_subgraph == 0): #we need to close a subgraph
				print "}"
			else:
				first_subgraph = 0
			print "subgraph" + " cluster" + table_name + " {"
			print "style=filled"
			print "color=lightgrey"
			print table_format
			print table_name
			print attr_format

		buffer = buffer[end:] # moving the iterator
		match = next(table_grammar.scanString(buffer), None)
	else: # we have encountered the inside of the CREATE/ALTER TABLE statement
		match = next(grammar.scanString(buffer), None) 
			
		while match: # we've found a standard attribute line
			tokens, start, end = match	

			if ((tokens[0] != sql_keyword) & (tokens[0] != open_para)): # get attribute name
				current_attr = table_name + underscore + tokens[0]
				if ('PRIMARY' in tokens.asList()):
					print current_attr + " [label=\"" + tokens[0] + "\", fontname=\"Courier-Bold\"]"
				else:
					print current_attr + " [label=\"" + tokens[0] + "\"]"
				print table_name + directed + current_attr + ""

			elif (tokens[0] == open_para): # another way to get attribute name (escape parathesis)
				current_attr = table_name + underscore + tokens[1]
				if ('PRIMARY' in tokens.asList()):
					print current_attr + " [label=\"" + tokens[0] + "\", fontname=\"Courier-Bold\"]"
				else:
					print current_attr + " [label=\"" + tokens[1] + "\"]"
				print table_name + directed + current_attr + ""


			reference_attr = []
			reference_attr.append(current_attr) #save the attribute in case we get REFERENCING on the next line

			buffer = buffer[end:]
			match = next(grammar.scanString(buffer), None)

		else: # check one of the other line cases
			match = next(reference_grammar.scanString(buffer), None)

			while match: # we've found a referencing line, for FKs
				tokens, start, end = match
				print key_format
				for s in reference_attr:
					print s + directed + tokens[1]
				print edge_format
				buffer = buffer[end:]
				match = next(reference_grammar.scanString(buffer), None)

			else:
				match = next(constraints.scanString(buffer), None)

				while match: # we've found a constraint line, for FKs and PKs
					tokens, start, end = match
					
					i = 6

					if (tokens[0] == "ADD"): # escape the leading ADD from alter table
						i = i+1
					if(tokens[i] == ","): #primary key
						i = i-1	
					reference_attr = []
					while (i < len(tokens)):
						if (('PRIMARY' in tokens.asList()) & (i < len(tokens) - 1)):
							print table_name + underscore + tokens[i] + " [fontname=\"Courier-Bold\"]"	
						reference_attr.append(table_name + underscore + tokens[i])
						i = i+2
					
					buffer = buffer[end:]
					match = next(constraints.scanString(buffer), None)	

print "}\n}"
