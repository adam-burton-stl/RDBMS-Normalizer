# RDBMS Normalizer
# By Adam Burton


import sys


class FunctionalDependency:
    determinant: list[str]
    dependents: list[str]

    def __init__(self, det: list[str], deps: list[str]):
        self.determinant = det
        self.dependents = deps

    def is_dep(self, attr):
        if attr in self.dependents:
            return True
        else:
            return False

    def remove_dep(self, attr):
        self.dependents.remove(attr)

    def det_contains(self, attrs):
        for i in range(len(attrs)):
            if attrs[i] in self.determinant:
                return True
        return False

    def __str__(self):
        """Pretty print of FunctionalDependency"""
        output = "{"
        for det in self.determinant[:-1]:
            output += det + ", "
        output += self.determinant[-1] + "} -> {"
        for dep in self.dependents[:-1]:
            output += dep + ", "
        output += self.dependents[-1] + "}"
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
            + (str(self.candidate_keys) if str(self.candidate_keys) else "None")
            + "\n"
        )
        result += "Multi-Valued Attributes: " + str(self.multivalued_attributes) + "\n"
        result += "Functional Dependencies:\n"
        if self.fds == []:
            result += "N/A\n"
        else:
            for i in range(len(self.fds)):
                result += str(self.fds[i]) + "\n"
        return result

    def one_nf(self):
        """Convert the relation into 1NF by separating all multivalued attributes into their own tables (which are returned)."""
        new_tables: list[Relation] = []
        for i in range(len(self.multivalued_attributes)):
            if self.multivalued_attributes[i] in [x[0] for x in self.attributes]:
                new_title = self.multivalued_attributes[i] + "Data"
                new_attrs = self.primary_key[:]
                new_attrs.append(self.multivalued_attributes[i])
                for j in range(len(new_attrs)):
                    loc = [x[0] for x in self.attributes].index(new_attrs[j])
                    new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                    if new_attrs[j][0] == self.multivalued_attributes[i]:
                        self.attributes.pop(loc)
                new_prim = self.primary_key[:]
                new_prim.append(self.multivalued_attributes[i])
                new_fds = []
                for j in range(len(self.fds)):
                    if self.fds[j].is_dep(self.multivalued_attributes[i]):
                        new_fds.append(
                            FunctionalDependency(
                                self.fds[j].determinant,
                                [self.multivalued_attributes[i]],
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
                        fds=new_fds,
                    )
                )
        self.multivalued_attributes = []
        return new_tables

    def two_nf(self):
        new_tables = []
        fds_to_remove = []
        # print("-" * 50)
        # print(f"From:\n{self}")

        for i in range(len(self.fds)):
            affected_attrs = []
            if (
                self.fds[i].det_contains(self.primary_key)
                and self.fds[i].determinant != self.primary_key
            ):
                try:
                    for dep in self.fds[i].dependents:
                        if dep not in self.primary_key:
                            affected_attrs.append(dep)
                            # print(
                            #     f"!!! PFD DETECTED in {self.name} for attribute {dep}!!!"
                            # )
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
                            loc = [x[0] for x in self.attributes].index(new_attrs[j])
                            new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                            if new_attrs[j][0] not in self.primary_key:
                                # print(
                                #     f"removing attribute {self.attributes[loc]} from {self.name}"
                                # )
                                self.attributes.pop(loc)

                        new_fds = [self.fds[i]]
                        for fd in self.fds[:i] + self.fds[i + 1 :]:
                            print("testing", str(fd))
                            for attr in affected_attrs:
                                if fd.det_contains([attr]) or (
                                    attr in fd.dependents
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
        # print("Created:")
        # for i in range(len(new_tables)):
        #     print(new_tables[i])
        # print("-" * 50)
        return new_tables

    def three_nf(self):
        new_tables = []
        all_dets = []
        all_deps = []
        for fd in self.fds:
            all_dets += fd.determinant
            all_deps += fd.dependents
        for fd in self.fds:
            for fd_dep in fd.dependents:
                if fd_dep in all_dets:
                    print(
                        f"!!!!!!Found transitive dependency from {fd_dep} in {self.name}"
                    )
        return new_tables


def interpret_input(filename: str) -> Relation:
    """Read the contents of the given file and create a corresponding Relation class instance."""
    schema = open(input_filename, "r")
    name = schema.readline().split()[1]
    if len(name) < 1:
        print("Error: Invalid relation name.")
        sys.exit()
    attributes = schema.readline()[12:-1].split(", ")
    if len(attributes) < 1:
        print("Error: Invalid attributes.")
        sys.exit()
    for i in range(len(attributes)):
        attributes[i] = attributes[i].split(":")
    primary_key = schema.readline()[13:-1]
    if (primary_key[0] == "{") and (primary_key[-1] == "}"):
        primary_key = primary_key[1:-1].split(", ")
        if len(primary_key) < 1:
            print("Error: No attributes in the primary key.")
            sys.exit()
    else:
        print("Error: Must include a primary key, surrounded by brackets.")
        sys.exit()
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

    mv_attrs = schema.readline()[25:-1].split(", ")
    fds: list[FunctionalDependency] = []
    if schema.readline()[:24] == "Functional Dependencies:":
        while fd := schema.readline():
            if fd == "N/A":
                break
            det, deps = fd.split(" -> ")
            if det[0] == "{" and det[-1] == "}":
                det = det[1:-1].split(", ")
            else:
                print("Error: Determinant must be surrounded by brackets.")
                sys.exit()
            deps = deps[:-1]
            if deps[0] == "{" and deps[-1] == "}":
                deps = deps[1:-1].split(", ")
            else:
                print("Error: Dependents must be surrounded by brackets.")
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
    print("Entering First normal form...")
    new_tables = tables[0].one_nf()
    if len(new_tables):
        tables += new_tables
    for i in range(len(tables)):
        print(tables[i])
    print("Time for Second Normal Form...")
    for x in tables:
        new_tables = x.two_nf()
        if len(new_tables):
            tables += new_tables
    print("-" * 50)
    for i in range(len(tables)):
        print(tables[i])
    print("Time for Third Normal Form...")
    for x in tables:
        new_tables = x.three_nf()
        if len(new_tables):
            tables += new_tables

    output_name = "normalized_schema.txt"
    if len(sys.argv) > 2:
        output_name = sys.argv[3]
    output_results(output_name, tables)
