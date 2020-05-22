import os
import csv
from flask import flash


def open_bed(bed, user_id, user_name, genome, technology):
    """Opens bed file to load into variants table."""

    if os.path.exists(bed) and os.path.getsize(bed) > 0:
        try:
            with open(bed, 'r') as f:
                dr = csv.reader(f, delimiter='\t')
                
                # See if bed has 4 columns:
                correct_number_columns = [False]
                for row in dr:
                    if len(row) < 4:
                        correct_number_columns.append(True)
                
            if True in correct_number_columns:
                to_db = "Not 4 columns"
                flash(".bed file requires 4 columns: chr\tstart\tend\tvariant_type.")
            else:
                with open(bed, 'r') as f:
                    dr = csv.reader(f, delimiter='\t')
                    # list of dicts:
                    to_db = [{
                              'genome':genome,
                              'chromosome':i[0], 
                              'sv_start':i[1], 
                              'sv_end':i[2], 
                              'variant':i[3],
                              'technology':technology
                              } for i in dr]
        except IOError:
            flash(".bed file does not exists or is not properly setup.")

    return to_db
