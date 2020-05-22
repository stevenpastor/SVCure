import os
import csv
from flask import flash


def batch_select(csvfile):
# def batch_select(csvfile, user_id, user_name, genome, technology):
    """Opens bed file to load into variants table."""

    if os.path.exists(csvfile) and os.path.getsize(csvfile) > 0:
        try:
            with open(csvfile, 'r') as f:
                dr = csv.reader(f, delimiter=',')
                
                # See if csv file has 7 columns:
                correct_number_columns = [False]
                for row in dr:
                    if len(row) < 7:
                        correct_number_columns.append(True)
                
            if True in correct_number_columns:
                to_db = "Not 7 columns"
                flash(".csv file requires 7 columns: Genome,Alignment Bam, Bai, Ref fasta, Ref build (e.g., hg38), Bed, and Technology (e.g., Illumina).")
            else:
                with open(csvfile, 'r') as f:
                    dr = csv.reader(f, delimiter=',')
                    to_db = [line for line in dr]
                    # list of dicts:
                    # to_db = [{
                    #           'genome':i[0],
                    #           'alignment':i[1], 
                    #           'alignment_index':i[2], 
                    #           'reference':i[3], 
                    #           'reference_build':i[4],
                    #           'variants':i[5],
                    #           'technology':i[6]
                    #           } for i in dr]
        except IOError:
            flash(".csv file does not exists or is not properly setup.")

    return to_db
