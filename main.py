# RDBMS Normalizer
# By Adam Burton


import sys
from typing import Self


class FunctionalDependency:
    determinant: list[str]
    dependents: list[str]

    def __init__(self, det: list[str], deps: list[list[str]]):
        self.determinant = det
        self.dependents = deps

    def is_dep(self, attr: str) -> bool:
        result = False
        for i in range(len(self.dependents)):
            if attr in self.dependents[i]:
                result = True
        return result

    def remove_dep(self, attr: str) -> None:
        for i in range(len(self.dependents)):
            if attr in self.dependents[i]:
                self.dependents[i].remove(attr)
        # self.dependents.remove(attr)

    def det_contains(self, attrs: list[str]) -> bool:
        for i in range(len(attrs)):
            if attrs[i] in self.determinant:
                return True
        return False

    def is_mv(self) -> bool:
        if len(self.dependents) == 1:
            return False
        else:
            return True

    def copy(self) -> Self:
        return FunctionalDependency(self.determinant, self.dependents)

    def __str__(self) -> str:
        """Pretty print of FunctionalDependency"""
        output = "{"
        for det in self.determinant[:-1]:
            output += det + ", "
        if len(self.dependents) == 1:
            output += self.determinant[-1] + "} -> {"
        else:
            output += self.determinant[-1] + "} ->> {"
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
    data: list[str]

    def __init__(self, name, attrs, prim_key, can_keys, mv_attrs, fds=[], data=[]):
        self.name = name
        self.attributes = attrs
        self.primary_key = prim_key
        self.candidate_keys = can_keys
        self.multivalued_attributes = mv_attrs
        self.fds = fds
        self.data = data

    def __str__(self) -> str:
        """Pretty print of Relation"""
        result = "Relation: " + self.name + "\n"

        result += "Attributes: "
        for attr, typ in self.attributes[:-1]:
            result += attr + ":" + typ + ", "
        result += self.attributes[-1][0] + ":" + self.attributes[-1][1] + "\n"

        result += "Primary Key: {"
        for attr in self.primary_key[:-1]:
            result += attr + ", "
        result += self.primary_key[-1] + "}\n"

        result += "Candidate Keys: "
        if self.candidate_keys:
            for attr_set in self.candidate_keys[:-1]:
                result += "{"
                for attr in attr_set[:-1]:
                    result += attr + ", "
                result += attr_set[-1] + "}, "
            result += "{"
            for attr in self.candidate_keys[-1][:-1]:
                result += attr + ", "
            result += self.candidate_keys[-1][-1] + "}\n"
        else:
            result += "None\n"

        result += "Multi-Valued Attributes: "
        if self.multivalued_attributes:
            for attr in self.multivalued_attributes[:-1]:
                result += attr + ", "
            result += self.multivalued_attributes[-1] + "}\n"
        else:
            result += "None\n"

        result += "Functional Dependencies:\n"
        if self.fds == []:
            result += "N/A\n"
        else:
            for i in range(len(self.fds)):
                result += str(self.fds[i]) + "\n"

        if self.data:
            result += "Data:\n"
            for tuple in self.data:
                for value in tuple[:-1]:
                    result += value + ", "
                result += tuple[-1] + "\n"
        return result

    def one_nf(self) -> list[Self]:
        """Normalize the relation to 1NF by separating all multivalued attributes into their own relations, which are returned."""
        print("Processing table", self.name, "...")
        fds_to_remove: list[int] = []
        new_tables: list[Relation] = []
        # Create a list of functional dependencies that are based on the primary key. These will be copied to any new relations
        # that contain the primary key.
        transferred_fds: list[FunctionalDependency] = []
        if len(self.multivalued_attributes):
            for fd in self.fds:
                keeper = True
                for attr in fd.determinant:
                    if attr not in self.primary_key:
                        keeper = False
                        break
                for dep_set in fd.dependents:
                    for attr in dep_set:
                        if attr not in self.primary_key:
                            keeper = False
                            break
                    if not keeper:
                        break
                if keeper:
                    transferred_fds.append(fd.copy())
        print("Identified keeper FDs")
        for keeper in transferred_fds:
            print(str(keeper))

        for i in range(len(self.multivalued_attributes)):
            print(f"Creating table for {self.multivalued_attributes[i]}...")
            if self.multivalued_attributes[i] in [x[0] for x in self.attributes]:
                new_title = self.multivalued_attributes[i] + "Data"
                new_prim = []
                new_can = []
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
                        table_based_on_fd = True
                        fds_to_remove.append(j)
                        break
                # If the removed attribute is not alone in an FD, separate by putting it in a new table with the old one's
                # primary key
                if not table_based_on_fd:
                    new_prim = self.primary_key[:]
                    new_prim.append(self.multivalued_attributes[i])
                    new_attrs = new_prim[:]
                # assign data types to new_attrs and actually remove the removed attribute from the old relation
                # (similar code will appear frequently in later normal forms)
                for j in range(len(new_attrs)):
                    loc = [x[0] for x in self.attributes].index(new_attrs[j])
                    new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
                    if new_attrs[j][0] == self.multivalued_attributes[i]:
                        self.attributes.pop(loc)

                # If the table wasn't based on an existing FD, move any matching FDs to the new table.
                if not table_based_on_fd:
                    print("this happened")
                    new_fds += transferred_fds
                    for j in range(len(self.fds)):
                        if self.fds[j].is_dep(self.multivalued_attributes[i]):
                            # new_fds.append(
                            #     FunctionalDependency(
                            #         self.fds[j].determinant,
                            #         [[self.multivalued_attributes[i]]],
                            #     )
                            # )
                            self.fds[j].remove_dep(self.multivalued_attributes[i])
                for key in self.candidate_keys:
                    transferable = True
                    for attr in key:
                        if attr not in [x[0] for x in new_attrs]:
                            transferable = False
                    if transferable:
                        new_can.append(key)
                new_tables.append(
                    Relation(
                        new_title,
                        new_attrs,
                        new_prim,
                        can_keys=new_can,
                        mv_attrs=[],
                        fds=new_fds,
                        data=[],
                    )
                )
        self.multivalued_attributes = []
        fds_to_remove.sort(reverse=True)
        for i in range(len(fds_to_remove)):
            self.fds.pop(fds_to_remove[i])

        for i in range(len(self.candidate_keys) - 1, 0, -1):
            for attr in self.candidate_keys[i]:
                if attr not in [x[0] for x in self.attributes]:
                    self.candidate_keys.pop(i)

        return new_tables

    def two_nf(self) -> list[Self]:
        """Normalize the relation to 2NF by detecting partial functional dependencies and separating them into new
        relations, which are returned."""
        new_tables = []
        fds_to_remove = []
        removed_attributes = []
        prime_attributes = self.primary_key[:]
        for key in self.candidate_keys:
            prime_attributes += key
        # TODO: Incorporate candidate keys as prime attributes
        # TODO: remove attributes from FD instead of killing the whole FD??

        for i in range(len(self.fds)):
            affected_attrs = []
            # If the FD's determinant contains a prime attribute, but not the entire primary key...
            if (
                (len(self.fds[i].dependents) == 1)
                and self.fds[i].det_contains(prime_attributes)
                and not (
                    self.fds[i].determinant == self.primary_key
                    or self.fds[i].determinant in self.candidate_keys
                )
            ):
                print(f"FD {self.fds[i]} has a partial prime attribute determinant")
                # try block because functional dependencies aren't removed until the end
                try:
                    # Locate non-prime attributes in the dependent of the FD
                    for attr in self.fds[i].dependents[0]:
                        if attr not in prime_attributes:
                            affected_attrs.append(attr)
                            print(
                                f"!!! PFD DETECTED in {self.name} for attribute {attr}!!!"
                            )
                    # If non-prime attributes were found, remove these attributes and create a new table.
                    if len(affected_attrs):
                        new_name = ""
                        for det in self.fds[i].determinant:
                            new_name += det
                        new_name += "Data"
                        new_attrs = self.fds[i].determinant[:]
                        new_attrs += affected_attrs
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
                                # If any functional dependency contains any affected attributes as a determinant or dependent,
                                # and all of the dependent attributes are in the new table...
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
                        new_can = []
                        for key in self.candidate_keys:
                            transferable = True
                            for attr in key:
                                if attr not in [x[0] for x in new_attrs]:
                                    transferable = False
                            if transferable:
                                new_can.append(key)
                        new_tables.append(
                            Relation(
                                name=new_name,
                                attrs=new_attrs,
                                prim_key=self.fds[i].determinant[:],
                                can_keys=new_can,
                                mv_attrs=[],
                                fds=new_fds,
                                data=[],
                            )
                        )
                        fds_to_remove.append(i)
                except:
                    print(end="")
        fds_to_remove.sort(reverse=True)
        for i in range(len(fds_to_remove)):
            self.fds.pop(fds_to_remove[i])

        for i in range(len(self.candidate_keys) - 1, 0, -1):
            for attr in self.candidate_keys[i]:
                if attr not in [x[0] for x in self.attributes]:
                    self.candidate_keys.pop(i)
        return new_tables

    def three_nf(self) -> list[Self]:
        """Normalize the relation to 3NF by detecting transitive functional dependencies and separating them into
        their own relations, which are returned."""
        new_tables = []
        fds_to_pop = []
        for i in range(len(self.fds)):
            # Ignore multi-valued dependencies
            if len(self.fds[i].dependents) > 1:
                continue
            # TODO: Check for superkey instead of primary key...
            # If an FD's determinant isn't the primary key and there are non-prime dependents, the FD is violates 3NF and
            # must be separated out.
            violation = False
            if set(self.primary_key) != set(self.fds[i].determinant):
                for dep in self.fds[i].dependents[0]:
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
                        data=[],
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
        # Remove all identified (and separated) transitive funcitonal dependencies
        for i in fds_to_pop[::-1]:
            self.fds.pop(i)
        return new_tables

    def bcnf(self) -> list[Self]:
        """Normalize the relation to BCNF by detecting functional dependencies with non-superkey determinants and
        separating them into their own relations, which are returned."""
        new_tables = []
        fds_to_pop = []
        for i in range(len(self.fds)):
            # Ignore multi-valued attributes
            if len(self.fds[i].dependents) > 1:
                continue
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
                # Add the violating FD's involved attributes to the new table (with their data types)
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
                        data=[],
                    )
                )
                # Remove the violating attributes from the old table
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
        # Remove all identified (and separated) violating functional dependencies
        for i in fds_to_pop[::-1]:
            self.fds.pop(i)
        print("-" * 50)
        return new_tables

    def four_nf(self) -> list[Self]:
        """Normalize the relation to 4NF by separating multivalued functional dependencies into their own relations,
        which are returned."""
        # TODO: Request if there are additional MVDs for each relation with enough attributes
        # TODO: Request data. split based on the newly supplied MVDs
        new_tables = []
        # Tables with less than 3 attributes automatically satisfy 4NF
        if len(self.attributes) < 3:
            return new_tables
        # For other 3+ attribute tables, request multivalue dependencies from the user
        print(f"\nHere is the schema for relation {self.name}:")
        print(str(self))
        print(
            "Are there any multi-valued dependencies you want to add before normalization?"
        )
        user_in = input("Type a multi-valued dependency or 'q':\n")
        while user_in != "q":
            valid = True
            if not (" ->> " in user_in):
                print("Invalid input: Must include '->>'. Please try again.")
                valid = False
            else:
                det, deps = user_in.split(" ->> ")
                deps = deps.split(" | ")
                if len(deps) < 2:
                    print(
                        "Invalid input: Only one dependent set provided. Please try again."
                    )
                    valid = False
                for i in range(len(deps)):
                    if deps[i][0] == "{" and deps[i][-1] == "}":
                        deps[i] = deps[i][1:-1].split(", ")
                    else:
                        print(
                            "Invalid input: Dependents must be surrounded by brackets. Please try again."
                        )
                        valid = False
                if det[0] == "{" and det[-1] == "}":
                    det = det[1:-1].split(", ")
                else:
                    print(
                        "Invalid input: Determinant must be surrounded by brackets. Please try again."
                    )
                    valid = False
                fd_attrs = det[:]
                for dep_set in deps:
                    fd_attrs += dep_set
                for attr in fd_attrs:
                    if not attr in [x[0] for x in self.attributes]:
                        print(
                            "Error: Attribute in functional dependency not present in attribute set. Please try again."
                        )
                        valid = False
            if valid:
                self.fds.append(FunctionalDependency(det, deps))
                print(f"The relation now has the following Functional Dependencies:")
                for fd in self.fds:
                    print(str(fd))

            user_in = input("Type a multi-valued dependency or 'q':\n")
        mvds = []
        for fd in self.fds:
            if len(fd.dependents) > 1:
                mvds.append(fd)
        # If there are no multi-valued dependencies, return here. Otherwise, proceed with requesting table data to verify.
        if not mvds:
            return new_tables
        print("This relation has the following MVDs:")
        for mvd in mvds:
            print(str(mvd))
        print("\nThe normalizer needs table data to verify.")
        print(
            "Please enter data values separated by ', ' that adhere to the following schema:"
        )
        for attr in [x[0] for x in self.attributes[:-1]]:
            print(attr, end=", ")
        print(self.attributes[-1][0])
        print("Each tuple is on its own line. Enter 'q' instead to stop input.")
        user_in = input()
        while user_in != "q":
            user_in = user_in.split(", ")
            if len(user_in) == len(self.attributes):
                self.data.append(user_in)
            else:
                print(
                    "Incorrect number of attributes. Please match the following schema or enter q to stop input."
                )
                for attr in [x[0] for x in self.attributes[:-1]]:
                    print(attr, end=", ")
                print(self.attributes[-1][0])
            user_in = input()
        print("\nData has been added to the relation!")
        print(str(self))

        # Validate MVDs

        # Separate MVDs
        # Select which MVD to use
        if len(mvds) > 1:
            print(
                "Which of the following MVDs should be prioritized for decomposition?"
            )
            for i in range(len(mvds)):
                print(f"{i+1}: {str(mvds[i])}")
            priority = input()
            while not priority.isnumeric() or not int(priority) <= len(mvds):
                print(f"Invalid input: enter a number between 1 and {len(mvds)}:")
                priority = input()
            priority = int(priority) - 1
        else:
            priority = 0

        chosen_fd = self.fds[priority]

        for dep_set in chosen_fd.dependents:
            new_name = ""
            for attr in chosen_fd.determinant:
                new_name += attr
            for attr in dep_set:
                new_name += attr
            new_name += "Data"
            new_attrs = chosen_fd.determinant[:] + dep_set

            # Handle Data transfer:
            used_attr_i = []
            for i in range(len(self.attributes)):
                if self.attributes[i][0] in new_attrs:
                    used_attr_i.append(i)
            new_data = []
            for tuple in self.data:
                new_tuple = []
                for i in used_attr_i:
                    new_tuple.append(tuple[i])
                duplicate = False
                for i in range(len(new_data)):
                    if set(new_tuple) == set(new_data[i]):
                        duplicate = True
                        break
                if not duplicate:
                    new_data.append(new_tuple)

            # Add data type info to attributes
            for j in range(len(new_attrs)):
                loc = [x[0] for x in self.attributes].index(new_attrs[j])
                new_attrs[j] = [new_attrs[j], self.attributes[loc][1]]
            for tuple in new_data:
                print(tuple)
            new_tables.append(
                Relation(
                    name=new_name,
                    attrs=new_attrs,
                    prim_key=[x[0] for x in new_attrs],
                    can_keys=[],
                    mv_attrs=[],
                    fds=[],
                    data=new_data,
                )
            )
            print(f"Created\n{new_tables[-1]}")
        return new_tables

    def five_nf(self) -> list[Self]:
        """Normalize the relation to 5NF by prompting for table data, analyzing for join dependencies, and splitting the
        relation into two new ones, which are returned (if the table can be split)."""
        # TODO: Actually do have to test every combination... ugh
        new_tables = []
        table_data = [[]]
        if len(self.attributes) > 2:
            # Data Entry
            print(
                f"Relation {self.name} has {len(self.attributes)} attributes and may be decomposed."
            )
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
                    table_data.append(user_in)
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

            # Computation

        else:
            print(
                f"Relation {self.name} only has 2 attributes and cannot be broken down."
            )
        return new_tables


def interpret_input(input_filename: str) -> Relation:
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
            fd_attrs = det[:]
            for dep_set in deps:
                fd_attrs += dep_set
            for attr in fd_attrs:
                if not attr in [x[0] for x in attributes]:
                    print(
                        "Error: Attribute in functional dependency not present in attribute set."
                    )
                    sys.exit()
            fds.append(FunctionalDependency(det, deps))
    schema.close()
    table = Relation(name, attributes, primary_key, candidate_keys, mv_attrs, fds=fds)
    return table


def output_results(filename: str, tables: list[Relation]) -> None:
    """Fill a specified output file with the given list of tables."""
    dest = open(filename, "w")
    for i in range(len(tables)):
        dest.write(str(tables[i]) + "\n\n")
    dest.close()


def remove_redundant_relations(tables: list[Relation]) -> list[Relation]:
    attr_sets: list[list[str]] = [[x[0] for x in tables[-1].attributes]]
    non_dupes: list[Relation] = [tables[-1]]
    for i in range(len(tables) - 2, 0, -1):
        attrs = [[x[0] for x in tables[-1].attributes]]
        if attrs in attr_sets:
            tables.pop(i)
        else:
            non_dupes.append(tables[i])
            attrs.append(attrs)
    return tables


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Please add an input file of the following form as a command-line argument and try again."
        )
        print(
            Relation(
                name="example",
                attrs=[["attr1", "VARCHAR(255)"], ["attr2", "INTEGER"]],
                prim_key=["attr1"],
                can_keys=[],
                mv_attrs=["attr2"],
                fds=[FunctionalDependency(["attr1"], [["attr2"]])],
                data=[],
            )
        )
        sys.exit()
    print(
        "Thank you for using the RDBMS Normalizer!\nPlease note that input file format must match the provided example inputs."
    )
    tables: list[Relation] = []
    input_filename = sys.argv[1]
    tables.append(interpret_input(input_filename))
    print(tables[0])

    user_in = input(
        'How far do you want to normalize the relation?\n(Enter one of the following: "1NF", "2NF", "3NF", "BCNF", "4NF", "5NF")\n'
    ).upper()
    while user_in not in ["1NF", "2NF", "3NF", "BCNF", "4NF", "5NF"]:
        user_in = input(
            'Invalid input, please enter one of the following: "1NF", "2NF", "3NF", "BCNF", "4NF", "5NF"\n'
        ).upper()
    print(f"You chose {user_in}.")

    print("Entering First normal form...")
    new_tables = tables[0].one_nf()
    if len(new_tables):
        tables += new_tables

    if user_in in ["2NF", "3NF", "BCNF", "4NF", "5NF"]:
        print("Time for Second Normal Form...")
        for x in tables:
            new_tables = x.two_nf()
            if len(new_tables):
                tables += new_tables
                tables += new_tables

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

    # Remove duplicate tables
    table_attr_sets: list[list[str]] = []
    for i in range(len(tables) - 1, 0, -1):
        my_attrs = [x[0] for x in tables[i].attributes]
        if not my_attrs in table_attr_sets:
            table_attr_sets.append(my_attrs)
        else:
            tables.pop(i)

    if user_in in ["4NF", "5NF"]:
        print("Time for Fourth Normal Form...")
        old_tables = []
        for x in tables:
            new_tables = x.four_nf()
            if len(new_tables):
                for table in new_tables:
                    my_attrs = [x[0] for x in table.attributes]
                    if not my_attrs in table_attr_sets:
                        tables += new_tables
                old_tables.append(tables.index(x))
        old_tables.sort(reverse=True)
        for i in old_tables:
            tables.pop(i)
        tables = remove_redundant_relations(tables)

    if user_in in ["5NF"]:
        print("Time for Fifth Normal Form...")
        print(
            "NOTE: This normal form requires data that will have to be entered for each relation."
        )
        for x in tables:
            new_tables = x.five_nf()
            if len(new_tables):
                tables += new_tables

    # Duplicate checking:
    # Remove duplicate tables
    table_attr_sets: list[set[str]] = []
    for i in range(len(tables) - 1, -1, -1):
        print("Curr attr sets")
        for attrs in table_attr_sets:
            print(attrs)
        my_attrs = [x[0] for x in tables[i].attributes]
        print(my_attrs, "?")
        if not (set(my_attrs) in table_attr_sets):
            table_attr_sets.append(set(my_attrs))
            print("Added to set")
        else:
            tables.pop(i)
            print("Nope")

    output_name = "normalized_schema.txt"
    if len(sys.argv) > 2:
        output_name = sys.argv[3]
    output_results(output_name, tables)
    print(f"The noramlized schema has been outputted to {output_name}")
    print("Thank you for using the RDBMS Normalizer!")
