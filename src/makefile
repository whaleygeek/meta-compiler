# build the meta-compiler engine.
#
# strip comments without changing line numbers
# and process it with the m2 machine for the appropriate language grammar

#----- TOOLS -----

DELCOMMENT = sed "s/^[ \t]*\/\/.*//"
META = ./meta.py
DIFF = diff
GCC = gcc -c -E
LINK = gcc


#----- GENERAL RULES -----

# Turn a C source file into an O object file
%.o : %.c
	$(GCC) $< -o $@

# Turn a spec source file into a meta file
.PRECIOUS: %.meta
%.meta: %.spec
	$(META) < $< > $@

# Turn a lang source program into a C program
.PRECIOUS: %.c
%.c: %.lang lang.meta
	$(DELCOMMENT) < $< | $(META) lang.meta > $@

# Turn a valgol1 source program into a C program
.PRECIOUS: %.c
%.c: %.valgol1 valgol1.meta
	$(DELCOMMENT) < $< | $(META) valgol1.meta > $@

# Link an object file into an executable
test%: test%.o
	$(LINK) $< -o $@


#----- TARGETS -----

TARGETS = self test1
all: $(TARGETS)

# Self compilation check
self:
	$(META) < meta.spec > meta.meta
	$(META) meta.meta < meta.spec > meta.self
	$(DIFF) meta.meta meta.self



# Tidy up the directory of any generated files
clean:
	rm -f *.meta *.res *.self *.c *.o $(TARGETS)


