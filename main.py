# RDBMS Normalizer
# By Adam Burton


import sys


class FunctionalDependency:
    determinant: list[str]
    dependents: list[str]

    def __init__(self, desc: str):
        det, deps = desc.split(" -> ")
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
        print("Det:", det)
        print("Deps:", deps)
        self.determinant = det
        self.dependents = deps

    def __str__(self):
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
    FDs: list[FunctionalDependency]

    def __init__(self, name, attrs, prim_key, can_keys, mv_attrs):
        self.name = name
        self.attributes = attrs
        self.primary_key = prim_key
        self.candidate_keys = can_keys
        self.multivalued_attributes = mv_attrs

    def __str__(self):
        result = "Relation: " + self.name + "\n"
        result += "Attributes: " + str(self.attributes) + "\n"
        result += "Primary Key: " + str(self.primary_key) + "\n"
        result += (
            "Candidate Keys: "
            + (str(self.candidate_keys) if str(self.candidate_keys) else "None")
            + "\n"
        )
        result += "Multi-Valued Attributes: " + str(self.multivalued_attributes)
        return result

    def one_nf(self):
        new_tables: list[Relation] = []
        for i in range(len(self.multivalued_attributes)):
            if self.multivalued_attributes[i] in self.attributes:
                new_title = self.multivalued_attributes[i] + "Data"
                new_attrs = self.primary_key[:]
                new_attrs.append(self.multivalued_attributes[i])
                new_tables.append(
                    Relation(new_title, new_attrs, self.primary_key[:], [], [])
                )
                self.attributes.remove(self.multivalued_attributes[i])
        self.multivalued_attributes = []
        return new_tables


def interpret_input(filename: str) -> Relation:
    schema = open(input_filename, "r")
    name = schema.readline().split()[1]
    if len(name) < 1:
        print("Error: Invalid relation name.")
        sys.exit()
    attributes = schema.readline()[12:-1].split(", ")
    if len(attributes) < 1:
        print("Error: Invalid attributes.")
        sys.exit()
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
    schema.close()
    table = Relation(name, attributes, primary_key, candidate_keys, mv_attrs)
    return table


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Please add an input file of the following form as a command-line argument and try again."
        )
        print("")
        sys.exit()
    tables: list[Relation] = []
    input_filename = sys.argv[1]
    tables.append(interpret_input(input_filename))
    print(tables[0])
    print("Entering First normal form...")
    tables[0].one_nf()
    print(tables[0])

    new_FD = "{primary, another} -> {nonPrime, otherAttr}\n"
    print("Testing fds: ")
    realFD = FunctionalDependency(new_FD)
    print(realFD)
