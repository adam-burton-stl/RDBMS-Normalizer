# RDBMS Normalizer
# By Adam Burton


import sys


class FunctionalDependency:
    determinant: list[str]
    dependents: list[str]

    def __init__(self, det: list[str], deps: list[list[str]]):
        self.determinant = det
        self.dependents = deps

    def is_dep(self, attr):
        result = False
        for i in range(len(self.dependents)):
            if attr in self.dependents[i]:
                result = True
        return result

    def remove_dep(self, attr):
        for i in range(len(self.dependents)):
            if attr in self.dependents[i]:
                self.dependents[i].remove(attr)
        # self.dependents.remove(attr)

    def det_contains(self, attrs):
        for i in range(len(attrs)):
            if attrs[i] in self.determinant:
                return True
        return False

    def is_mv(self):
        if len(self.dependents) == 1:
            return False
        else:
            return True

    def __str__(self):
        """Pretty print of FunctionalDependency"""
        output = "{"
        for det in self.determinant[:-1]:
            output += det + ", "
        output += self.determinant[-1] + "} -> {"
        if len(self.dependents) == 1:
            for dep in self.dependents[0][:-1]:
                output += dep + ", "
            output += self.dependents[0][-1] + "}"
        else:
            for i in range(len(self.dependents))[:-1]:
                for dep in self.dependents[i][:-1]:
                    output += dep + ", "
                output += self.dependents[i][-1] + "}"
                output += " | "
            if output[-1] != "{":
                output += "{"
            for dep in self.dependents[-1][:-1]:
                output += dep + ", "
            output += self.dependents[-1][-1] + "}"
        return output


class Relation:
    name: str
    attributes: list[str]
    primary_key: list[str]
    candidate_keys: list[list[str]]
    multivalued_attributes: list[str]
    fds: list[FunctionalDependency]

    def __init__(self, name, attrs, prim_key, can_keys, mv_attrs, fds=[]):
        self.name = name
        self.attributes = attrs
        self.primary_key = prim_key
        self.candidate_keys = can_keys
        self.multivalued_attributes = mv_attrs
        self.fds = fds

    def __str__(self):
        """Pretty print of Relation"""
        result = "Relation: " + self.name + "\n"
        result += "Attributes: " + str(self.attributes) + "\n"
        result += "Primary Key: " + str(self.primary_key) + "\n"
        result += (
            "Candidate Keys: "
            + (str(self.candidate_keys) if len(self.candidate_keys) else "None")
            + "\n"
        )
        result += (
            "Multi-Valued Attributes: "
            + (
                str(self.multivalued_attributes)
                if len(self.multivalued_attributes)
                else "None"
            )
            + "\n"
        )
        result += "Functional Dependencies:\n"
        if self.fds == []:
            result += "N/A\n"
        else:
            for i in range(len(self.fds)):
                result += str(self.fds[i]) + "\n"
        return result

    def one_nf(self):
        """Convert the relation into 1NF by separating all multivalued attributes into their own tables (which are returned)."""
        print("Processing table", self.name, "...")
        fds_to_remove = []
        new_tables: list[Relation] = []
        for i in range(len(self.multivalued_attributes)):
            print(f"Creating table for {self.multivalued_attributes[i]}...")
            if self.multivalued_attributes[i] in [x[0] for x in self.attributes]:
                new_title = self.multivalued_attributes[i] + "Data"
                new_prim = []
                new_attrs = []
                new_fds = []
                # if removed attribute is alone in a functional dependency, separate based on the dependency
                # instead of the primary key
                table_based_on_fd = False
                print(
                    f"Testing for presence of {[[self.multivalued_attributes[i]]]} in FDs"
                )
                for j in range(len(self.fds)):
                    if self.fds[j].dependents == [[self.multivalued_attributes[i]]]:
                        new_prim = self.fds[j].determinant[:]
                        new_prim.append(self.multivalued_attributes[i])
                        new_attrs = new_prim[:]
                        new_fds.append(self.fds[j])
                        table_based_on_fd = True
                        fds_to_remove.append(j)
                        break
                if not table_based_on_fd:
                    new_prim = self.primary_key[:]
                    new_prim.append(self.multivalued_attributes[i])
                    new_attrs = new_prim[:]
                # assign data types to new_attrs
                for j in range(len(new_attrs)):
                    loc = [x[0] for x in self.attributes].index(new_attrs[j])
                    new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                    if new_attrs[j][0] == self.multivalued_attributes[i]:
                        self.attributes.pop(loc)

                if not table_based_on_fd:
                    for j in range(len(self.fds)):
                        if self.fds[j].is_dep(self.multivalued_attributes[i]):
                            new_fds.append(
                                FunctionalDependency(
                                    self.fds[j].determinant,
                                    [[self.multivalued_attributes[i]]],
                                )
                            )
                            self.fds[j].remove_dep(self.multivalued_attributes[i])
                new_tables.append(
                    Relation(
                        new_title,
                        new_attrs,
                        new_prim,
                        can_keys=[],
                        mv_attrs=[],
                        fds=[],
                    )
                )
        self.multivalued_attributes = []
        fds_to_remove.sort(reverse=True)
        for i in range(len(fds_to_remove)):
            self.fds.pop(fds_to_remove[i])
        return new_tables

    def two_nf(self):
        new_tables = []
        fds_to_remove = []
        removed_attributes = []

        for i in range(len(self.fds)):
            affected_attrs = []
            # If the functional dependency contains a prime attribute, but not the entire primary key...
            if (
                self.fds[i].det_contains(self.primary_key)
                and self.fds[i].determinant != self.primary_key
            ):
                print(f"FD {self.fds[i]} has a prime attribute determinant")
                try:
                    # Locate non-prime attributes in the dependent of the FD
                    for j in range(len(self.fds[i].dependents)):
                        for dep in self.fds[i].dependents[j]:
                            if dep not in self.primary_key:
                                affected_attrs.append(dep)
                                print(
                                    f"!!! PFD DETECTED in {self.name} for attribute {dep}!!!"
                                )
                    # If non-prime attribtues were found, remove these attributes and create a new table.
                    if len(affected_attrs):
                        new_name = ""
                        for det in self.fds[i].determinant:
                            new_name += det
                        new_name += "Data"
                        # print(f"Creating new relation {new_name}")
                        new_attrs = self.fds[i].determinant[:]
                        new_attrs += affected_attrs
                        # print(f"Contains attributes: {new_attrs}")
                        for j in range(len(new_attrs)):
                            # Reformat attributes to have data type and remove them from their old table
                            loc = [x[0] for x in self.attributes].index(new_attrs[j])
                            new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                            if new_attrs[j][0] not in self.primary_key:
                                print(
                                    f"removing attribute {self.attributes[loc]} from {self.name}"
                                )
                                removed_attributes.append(self.attributes[loc])
                                self.attributes.pop(loc)
                        # Incorporate the base functional dependency, and any others that involve the affected attributes
                        new_fds = [self.fds[i]]
                        for fd in self.fds[:i] + self.fds[i + 1 :]:
                            print("testing", str(fd))
                            for attr in affected_attrs:
                                unpacked_dependents = []
                                for dep_set in fd.dependents:
                                    unpacked_dependents += dep_set
                                # If a functional dependency contains target attribute as a determinant or dependent,
                                # and all of the determinant's attributes are in the new table...
                                if fd.det_contains([attr]) or (
                                    attr in unpacked_dependents
                                    and (
                                        False
                                        not in [
                                            (x in [y[0] for y in new_attrs])
                                            for x in fd.determinant
                                        ]
                                    )
                                ):
                                    new_fds.append(fd)
                                    fds_to_remove.append(self.fds.index(fd))
                                    print(
                                        f"Transferring {str(fd)} from {self.name} to {new_name}"
                                    )
                                    break
                        new_tables.append(
                            Relation(
                                name=new_name,
                                attrs=new_attrs,
                                prim_key=self.fds[i].determinant[:],
                                can_keys=[],
                                mv_attrs=[],
                                fds=new_fds,
                            )
                        )
                        fds_to_remove.append(i)
                except:
                    print(end="")
        fds_to_remove.sort(reverse=True)
        for i in range(len(fds_to_remove)):
            self.fds.pop(fds_to_remove[i])

        print(f"Relation {self.name} - Total removed attributes:", removed_attributes)
        for i in range(len(removed_attributes)):
            for j in range(len(self.fds)):
                if removed_attributes[i][0] in self.fds[j].dependents:
                    print(f"Removing {removed_attributes[i]} from {self.fds[j]}")
                    self.fds[j].remove_dep(removed_attributes[i][0])
        return new_tables

    def three_nf(self):
        new_tables = []
        fds_to_pop = []
        for i in range(len(self.fds)):
            # If any attributes of the FD's determinant are dependents in another FD,
            # the FD is transitive, and must be separated out.
            violation = False
            if set(self.primary_key) != set(self.fds[i].determinant):
                for dep_set in self.fds[i].dependents:
                    for dep in dep_set:
                        if not (dep in self.primary_key):
                            violation = True
                            print(
                                f"!!!!!!Found transitive dependency from {dep} in {self.name}"
                            )

            if violation:
                new_name = ""
                for det in self.fds[i].determinant:
                    new_name += det
                new_name += "Data"
                print(f"Creating new relation {new_name}")
                # Add the transitive FD's involved attributes to the new table (with their data types)
                new_attrs = self.fds[i].determinant[:]
                for j in range(len(self.fds[i].dependents)):
                    new_attrs += self.fds[i].dependents[j][:]
                for j in range(len(new_attrs)):
                    loc = [x[0] for x in self.attributes].index(new_attrs[j])
                    new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                print(f"Contains attributes: {new_attrs}")
                new_tables.append(
                    Relation(
                        name=new_name,
                        attrs=new_attrs,
                        prim_key=self.fds[i].determinant[:],
                        can_keys=[],
                        mv_attrs=[],
                        fds=[self.fds[i]],
                    )
                )
                # Remove the transitively dependent attributes from the old table
                unpacked_deps = []
                for dep_set in self.fds[i].dependents:
                    unpacked_deps += dep_set
                for fd_dep in unpacked_deps:
                    print(
                        "popping:",
                        self.attributes.pop(
                            [x[0] for x in self.attributes].index(fd_dep)
                        ),
                    )
                fds_to_pop.append(i)
        # Remove all identified (and separated) transitive dependencies
        for i in fds_to_pop[::-1]:
            self.fds.pop(i)
        return new_tables

    def bcnf(self):
        new_tables = []
        fds_to_pop = []
        for i in range(len(self.fds)):
            # If the FD's determinant isn't a superkey, the FD violates BCNF and must be separated out.
            if set(self.primary_key) != set(self.fds[i].determinant):
                print(
                    f"Table {self.name}: PK = {self.primary_key}, FD {str(self.fds[i])} violates"
                )
                new_name = ""
                for det in self.fds[i].determinant:
                    new_name += det
                new_name += "Data"
                print(f"Creating new relation {new_name}")
                # Add the transitive FD's involved attributes to the new table (with their data types)
                new_attrs = self.fds[i].determinant[:]
                for j in range(len(self.fds[i].dependents)):
                    new_attrs += self.fds[i].dependents[j][:]
                for j in range(len(new_attrs)):
                    loc = [x[0] for x in self.attributes].index(new_attrs[j])
                    new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                print(f"Contains attributes: {new_attrs}")
                new_tables.append(
                    Relation(
                        name=new_name,
                        attrs=new_attrs,
                        prim_key=self.fds[i].determinant[:],
                        can_keys=[],
                        mv_attrs=[],
                        fds=[self.fds[i]],
                    )
                )
                # Remove the transitively dependent attributes from the old table
                unpacked_deps = []
                for dep_set in self.fds[i].dependents:
                    unpacked_deps += dep_set
                for fd_dep in unpacked_deps:
                    print(
                        "popping:",
                        self.attributes.pop(
                            [x[0] for x in self.attributes].index(fd_dep)
                        ),
                    )
                fds_to_pop.append(i)
        # Remove all identified (and separated) transitive dependencies
        for i in fds_to_pop[::-1]:
            self.fds.pop(i)
        print("-" * 50)
        return new_tables

    def four_nf(self):
        new_tables = []
        for fd in self.fds:
            # If there is a multi-valued dependency...
            if len(fd.dependents) > 1:
                # Create a new relation for each dependent set
                for dep_set in fd.dependents:
                    new_name = ""
                    for attr in fd.determinant:
                        new_name += attr
                    for attr in dep_set:
                        new_name += attr
                    new_name += "Data"
                    new_attrs = fd.determinant[:]
                    new_attrs += dep_set
                    new_prim = new_attrs[:]
                    for j in range(len(new_attrs)):
                        loc = [x[0] for x in self.attributes].index(new_attrs[j])
                        new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                    new_tables.append(
                        Relation(
                            name=new_name,
                            attrs=new_attrs,
                            prim_key=new_prim,
                            can_keys=[],
                            mv_attrs=[],
                            fds=[],
                        )
                    )
                    print(f"Created\n{new_tables[-1]}")
        return new_tables

    def five_nf(self):
        new_tables = []
        table_data = [[]]
        if len(self.attributes) > 2:
            print(
                "Please enter comma separated data that adheres to the following schema:"
            )
            for attr in [x[0] for x in self.attributes[:-1]]:
                print(attr, end=", ")
            print(self.attributes[-1][0])
            print("Each tuple is on its own line. Enter 'q' instead to stop input.")
            user_in = input()
            while user_in != "q":
                user_in = user_in.split()
                if len(user_in) == len(self.attributes):
                    table_data.insert(user_in)
                else:
                    print(
                        "Incorrect number of attributes. Please match the following schema or enter q to stop input."
                    )
                    for attr in [x[0] for x in self.attributes[:-1]]:
                        print(attr, end=", ")
                    print(self.attributes[-1][0])
                user_in = input()
            print("Input complete. You entered:")
            for tuple in table_data:
                print(tuple)
        else:
            print(
                f"Relation {self.name} only has 2 attributes and cannot be broken down."
            )
        return new_tables


def interpret_input(filename: str) -> Relation:
    """Read the contents of the given file and create a corresponding Relation class instance."""
    schema = open(input_filename, "r")
    # -- Name --
    name = schema.readline().split()[1]
    if len(name) < 1:
        print("Error: Invalid relation name.")
        sys.exit()
    # -- Attributes --
    attributes = schema.readline()[12:-1].split(", ")
    if len(attributes) < 1:
        print("Error: Invalid attributes.")
        sys.exit()
    for i in range(len(attributes)):
        attributes[i] = attributes[i].split(":")
    # -- Primary Key --
    primary_key = schema.readline()[13:-1]
    if (primary_key[0] == "{") and (primary_key[-1] == "}"):
        primary_key = primary_key[1:-1].split(", ")
        if len(primary_key) < 1:
            print("Error: No attributes in the primary key.")
            sys.exit()
    else:
        print("Error: Must include a primary key, surrounded by brackets.")
        sys.exit()
    # -- Candidate Keys --
    candidate_keys = schema.readline()[16:-1].split("}, ")
    if candidate_keys == ["None"]:
        candidate_keys = []
    elif len(candidate_keys):
        for i in range(len(candidate_keys)):
            if candidate_keys[i][0] == "{":
                candidate_keys[i] = candidate_keys[i][1:].split(", ")
            else:
                print("Error: Candidate key attributes must be surrounded by brackets.")
                sys.exit()
        candidate_keys[-1][-1] = candidate_keys[-1][-1][:-1]
    else:
        print(
            "Error: Candidate key definition is missing (use 'None' if there are none)."
        )
        sys.exit()
    # -- Multi-Value Attributes --
    mv_attrs = schema.readline()[25:-1].split(", ")
    # -- Functional Dependencies --
    fds: list[FunctionalDependency] = []
    if schema.readline()[:24] == "Functional Dependencies:":
        while fd := schema.readline():
            if fd == "N/A":
                break
            if " -> " in fd:
                det, deps = fd.split(" -> ")
                deps = deps[:-1]
                if deps[0] == "{" and deps[-1] == "}":
                    deps = [deps[1:-1].split(", ")]
                else:
                    print("Error: Dependents must be surrounded by brackets.")
                    sys.exit()
            elif " ->> " in fd:
                det, deps = fd.split(" ->> ")
                deps = deps[:-1].split(" | ")
                for i in range(len(deps)):
                    if deps[i][0] == "{" and deps[i][-1] == "}":
                        deps[i] = deps[i][1:-1].split(", ")
                    else:
                        print("Error: Dependents must be surrounded by brackets.")
                        sys.exit()
            else:
                print("Error: Functional Dependency requires '->' or '->>'")
            if det[0] == "{" and det[-1] == "}":
                det = det[1:-1].split(", ")
            else:
                print("Error: Determinant must be surrounded by brackets.")
                sys.exit()

            fds.append(FunctionalDependency(det, deps))
    schema.close()
    table = Relation(name, attributes, primary_key, candidate_keys, mv_attrs, fds=fds)
    return table


def output_results(filename, tables):
    dest = open(filename, "w")
    for i in range(len(tables)):
        dest.write(str(tables[i]) + "\n\n")
    dest.close()


if __name__ == "__main__":

    # TODO: add input choice to determine highest desired normal form.
    if len(sys.argv) < 2:
        print(
            "Please add an input file of the following form as a command-line argument and try again."
        )
        print("")
        sys.exit()
    print(
        "Thank you for using the RDBMS Normalizer!\nPlease note that input file format must match the provided example inputs."
    )
    tables: list[Relation] = []
    input_filename = sys.argv[1]
    tables.append(interpret_input(input_filename))
    print(tables[0])

    user_in = input(
        'How far do you want to normalize the relation?\n(Enter one of the following: "1NF", "2NF", "3NF", "BCNF", "4NF", "5NF")'
    )
    while user_in not in ["1NF", "2NF", "3NF", "BCNF", "4NF", "5NF"]:
        user_in = input(
            'Invalid input, please enter one of the following: "1NF", "2NF", "3NF", "BCNF", "4NF", "5NF"'
        )
    print(f"You chose {user_in}")

    print("Entering First normal form...")
    new_tables = tables[0].one_nf()
    if len(new_tables):
        tables += new_tables
    for i in range(len(tables)):
        print(tables[i])
    if user_in in ["2NF", "3NF", "BCNF", "4NF", "5NF"]:
        print("Time for Second Normal Form...")
        for x in tables:
            new_tables = x.two_nf()
            if len(new_tables):
                tables += new_tables
        print("-" * 50)
        for i in range(len(tables)):
            print(tables[i])
    if user_in in ["3NF", "BCNF", "4NF", "5NF"]:
        print("Time for Third Normal Form...")
        for x in tables:
            new_tables = x.three_nf()
            if len(new_tables):
                tables += new_tables
    if user_in in ["BCNF", "4NF", "5NF"]:
        print("Time for Boyce-Codd Normal Form... (not really)")
        # for x in tables:
        #     new_tables = x.bcnf()
        #     if len(new_tables):
        #         tables += new_tables

    if user_in in ["4NF", "5NF"]:
        print("Time for Fouth Normal Form...")
        tables_to_remove = []
        for x in tables:
            new_tables = x.four_nf()
            if len(new_tables):
                tables += new_tables
                tables_to_remove.append(tables.index(x))
        tables_to_remove.sort(reverse=True)
        for i in tables_to_remove:
            tables.pop(i)
    if user_in in ["5NF"]:
        print("Time for Fifth Normal Form...")
        print(
            "NOTE: This normal form requires data that will have to be entered for each relation."
        )

    output_name = "normalized_schema.txt"
    if len(sys.argv) > 2:
        output_name = sys.argv[3]
    output_results(output_name, tables)
