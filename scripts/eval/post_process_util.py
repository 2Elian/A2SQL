import re

input_file = "./predictions.sql"
output_file = "./output.sql"

column_pattern = re.compile(
    r'(?<!\')"(?!\')([^"]*[一-龥（）()/％%]+[^"]*)"'
)

with open(input_file, "r", encoding="utf-8") as fin, \
     open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        new_line = column_pattern.sub(r"\1", line)
        fout.write(new_line)

print("Done. Column name quotes removed.")
