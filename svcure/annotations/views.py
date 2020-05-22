from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort

from os import listdir
from os.path import isfile, join

from svcure import db
from svcure.auth.views import login_required
from svcure.annotations.models import StaticFiles, Genomes, Variants, Annotations
from svcure.auth.models import User
from svcure.annotations.forms import DetectForm#, prepopulate_form
from svcure.helpers.open_bed import open_bed
from svcure.helpers.batch_select import batch_select

# executemany:
from sqlalchemy.sql.expression import bindparam
# group_concat:
from sqlalchemy import func

# sqlalchemy-datatables: 
from datatables import ColumnDT, DataTables

# wtforms for pre-populating annotations forms:
from wtforms import RadioField, BooleanField, TextAreaField


bp = Blueprint("annotations", __name__)


@bp.route("/")
def index():
    """Homepage."""
    return render_template("annotations/index.html")


# @bp.route("/create", methods=("GET", "POST"))
# @login_required
# def create():
#     """Create a new annotation for the current user."""
#     if request.method == "POST":
#         title = request.form["title"]
#         body = request.form["body"]
#         error = None

#         if not title:
#             error = "Title is required."

#         if error is not None:
#             flash(error)
#         else:
#             db.session.add(Annotations(title=title, body=body, author=g.user))
#             db.session.commit()
#             return redirect(url_for("annotations.index"))

#     return render_template("annotations/create.html")


# @bp.route("/<int:id>/delete", methods=("POST",))
# @login_required
# def delete(id):
#     """Delete an annotation.

#     Ensures that the annotation exists and that the logged in user is the
#     author of the annotation.
#     """
#     annotation = get_annotation(id)
#     db.session.delete(annotation)
#     db.session.commit()
#     return redirect(url_for("annotations.index"))


#######################################################
@bp.route("/load_annotations", methods=("GET", "POST"))
@login_required
def load_annotations():
    """Load annotations if the current user is logged-in."""

    if request.method == "POST":
        
        # Batch Input:
        if 'batch_annotations' in request.form:

            # HERE: batch select function:
            annotation_csv = batch_select(request.form["batch_annotations"])
            for record in annotation_csv:
                # define variables:
                genome = record[0]
                alignment = record[1]
                alignment_index = record[2]
                reference = record[3]
                reference_build = record[4]
                variants = record[5]
                technology = record[6]

                # insert into static_files table:
                insert_command = StaticFiles.__table__.insert(
                    prefixes=['OR IGNORE'],
                    values=dict(
                                genome=genome,
                                alignment=alignment,
                                alignment_index=alignment_index,
                                reference=reference,
                                reference_build=reference_build,
                                variants=variants,
                                technology=technology
                                )
                )
                db.session.execute(insert_command)
                db.session.commit()

                # Load bed file into variants table:
                temp_data = open_bed("svcure/static/data/public/"+variants, 
                                    g.user.id,
                                    g.user.username, 
                                    genome,
                                    technology)

                # executemany:
                # check if genome exists in variants table:
                genome_exists = db.session.query(Variants.genome == genome).first()
                if genome_exists != None:
                    if False in genome_exists:
                        print("inside none")
                        print(genome,alignment,variants,technology)
                        # insert into the variants table:
                        statement = Variants.__table__.insert().prefix_with('OR IGNORE').values({
                                'genome' : bindparam('genome'),
                                'chromosome' : bindparam('chromosome'),
                                'sv_start' : bindparam('sv_start'),
                                'sv_end' : bindparam('sv_end'),
                                'variant' : bindparam('variant'),
                                'technology' : bindparam('technology'),
                                })
                        db.session.execute(statement, temp_data)
                        db.session.commit()
                    if False not in genome_exists:
                        print("inside if")
                        print(genome,alignment,variants,technology)
                        # get first instance of temp_data[technology]:
                        tech_instance = temp_data[0]['technology']
                        # get first instance of variants.technology where variants.genome == genome:
                        current_tech = db.session.query(Variants).filter(Variants.genome == genome).first().technology
                        # update variants.technology where variants.genome == genome:
                        db.session.query(Variants).filter(
                            Variants.genome == genome
                        ).update({Variants.technology:current_tech+','+tech_instance} 
                        )
                        db.session.commit()
                else:
                    print("inside else")
                    print(genome,alignment,variants,technology)
                    # insert into the variants table:
                    statement = Variants.__table__.insert().prefix_with('OR IGNORE').values({
                            'genome' : bindparam('genome'),
                            'chromosome' : bindparam('chromosome'),
                            'sv_start' : bindparam('sv_start'),
                            'sv_end' : bindparam('sv_end'),
                            'variant' : bindparam('variant'),
                            'technology' : bindparam('technology'),
                            })
                    db.session.execute(statement, temp_data)
                    db.session.commit()

                # Insert unique genomes into table:
                insert_command = Genomes.__table__.insert(
                    prefixes=['OR IGNORE'],
                    values=dict(genome=genome)
                )
                db.session.execute(insert_command)
                db.session.commit()
            
            return redirect(url_for("annotations.index"))
        
        # Single input:
        else:
            genome = request.form["genome"]
            alignment = request.form["alignment"]
            alignment_index = request.form["alignment_index"]
            reference = request.form["reference"]
            reference_build = request.form["reference_build"]
            variants = request.form["variants"]
            technology = request.form["technology"]
            error = None

            if not genome or not alignment or not alignment_index \
                or not reference or not reference_build or not variants \
                    or not technology:
                error = "All fields required."

            if error is not None:
                flash(error)
            
            else:
                # insert into static_files table:
                insert_command = StaticFiles.__table__.insert(
                    prefixes=['OR IGNORE'],
                    values=dict(
                                # user_id=g.user.id,
                                genome=genome,
                                alignment=alignment,
                                alignment_index=alignment_index,
                                reference=reference,
                                reference_build=reference_build,
                                variants=variants,
                                technology=technology
                                )
                )
                db.session.execute(insert_command)
                db.session.commit()
                
                # Load bed file into variants table:
                temp_data = open_bed("svcure/static/data/public/"+variants, 
                                    g.user.id,
                                    g.user.username, 
                                    genome,
                                    technology)

                # executemany:
                # check if genome exists in variants table:
                genome_exists = db.session.query(Variants.genome == genome).first()
                if genome_exists != None:
                    # get first instance of temp_data[technology]:
                    tech_instance = temp_data[0]['technology']
                    # get first instance of variants.technology where variants.genome == genome:
                    current_tech = db.session.query(Variants).filter(Variants.genome == genome).first().technology
                    # update variants.technology where variants.genome == genome:
                    db.session.query(Variants).filter(
                        Variants.genome == genome
                    ).update({Variants.technology:current_tech+','+tech_instance} 
                    )
                    db.session.commit()
                else:
                    # insert into the variants table:
                    statement = Variants.__table__.insert().prefix_with('OR IGNORE').values({
                            'genome' : bindparam('genome'),
                            'chromosome' : bindparam('chromosome'),
                            'sv_start' : bindparam('sv_start'),
                            'sv_end' : bindparam('sv_end'),
                            'variant' : bindparam('variant'),
                            'technology' : bindparam('technology'),
                            })
                    db.session.execute(statement, temp_data)
                    db.session.commit()

                # Insert unique genomes into table:
                insert_command = Genomes.__table__.insert(
                    prefixes=['OR IGNORE'],
                    values=dict(genome=genome)
                )
                db.session.execute(insert_command)
                db.session.commit()
                
                return redirect(url_for("annotations.index"))

    # Get files in static already:
    static_dir = "svcure/static/data/public"
    static_files = [f for f in listdir(static_dir) if isfile(join(static_dir, f))]

    # Get files in staticfiles tables already:
    staticfiles_table = StaticFiles.query.order_by(StaticFiles.genome.desc()).all()

    return render_template("annotations/load_annotations.html", 
                           static_files=static_files, 
                           staticfiles_table=staticfiles_table)


#######################################################




#######################################################
@bp.route("/loaded_genomes")
@login_required
def loaded_genomes():
    """Unique genome names loaded via load_annotations form(s)."""
    return render_template("annotations/loaded_genomes.html")


@bp.route('/genome_data')
def genome_data():
    """Return server side data for loaded_genomes."""
    columns = [
        ColumnDT(Genomes.genome)
    ]

    query = db.session.query().select_from(Genomes)
    params = request.args.to_dict()
    rowTable = DataTables(params, query, columns)
    data = rowTable.output_result()

    return jsonify(data)


# Filtering the table after click a genome:
@bp.route("/loaded_genomes", methods=("GET", "POST"))
@login_required
def my_form_post():
    # Get genome_name from HTML, input name=text:
    genome_name = request.form['text']
    return redirect(url_for('annotations.loaded_annotations', genome=genome_name))

#######################################################




#######################################################
@bp.route("/<string:genome>/loaded_annotations", methods=("GET", "POST"))
@login_required
def loaded_annotations(genome):
    """Loads annotations for <genome>."""

    # obtain technologies for the genome:
    all_techs = StaticFiles.query.filter(StaticFiles.genome == genome).all()

    # set to true only if exist; this is for column visibility in datatables:
    bionano,illumina,nanopore,pacbio,tenx = 'false','false','false','false','false'
    for tech in all_techs:
        if tech.technology.lower() == "bionano":
            bionano = 'true'
        elif tech.technology.lower() == "illumina":
            illumina = 'true'
        elif tech.technology.lower() == "nanopore":
            nanopore = 'true'
        elif tech.technology.lower() == "pacbio":
            pacbio = 'true'
        elif tech.technology.lower() == "tenx":
            tenx = 'true'

    # get current user so only they get link to annotate their annotation:
    username = g.user.username

    return render_template("annotations/loaded_annotations.html", 
                           genome=genome,
                           bionano=bionano,
                           illumina=illumina,
                           pacbio=pacbio,
                           nanopore=nanopore,
                           tenx=tenx,
                           username=username,
                           )








# from flask import send_file # download serverside, paginated table
from io import StringIO
import csv
from flask import make_response
@bp.route('/<string:genome>/download')
def download(genome):
    si = StringIO()
    cw = csv.writer(si)

    query = db.session.query(
        Variants.genome,
        Annotations.user_name,
        Variants.chromosome,
        Variants.sv_start,
        Variants.sv_end,
        Variants.variant,
        Annotations.bionano_presence,
        Annotations.bionano_depth,
        Annotations.bionano_partial,
        Annotations.bionano_spanning,
        Annotations.illumina_presence,
        Annotations.illumina_depth,
        Annotations.illumina_paired_end,
        Annotations.illumina_soft_clipped,
        Annotations.illumina_split_read,
        Annotations.nanopore_presence,
        Annotations.nanopore_depth,
        Annotations.nanopore_soft_clipped,
        Annotations.nanopore_split_read,
        Annotations.pacbio_presence,
        Annotations.pacbio_depth,
        Annotations.pacbio_soft_clipped,
        Annotations.pacbio_split_read,
        Annotations.tenx_presence,
        Annotations.tenx_depth,
        Annotations.tenx_soft_clipped,
        Annotations.tenx_split_read,
        Annotations.tenx_linked_read,
        Annotations.comments,
        Variants.id
    ).select_from(
        Variants
    ).outerjoin(
        Annotations, Annotations.variant_id == Variants.id
    ).filter(
        Variants.genome == genome
    )

    csvList = [i for i in query]
    csvList.insert(0, [
        "genome",
        "user_name",
        "chromosome",
        "sv_start",
        "sv_end",
        "variant",
        "bionano_presence",
        "bionano_depth",
        "bionano_partial",
        "bionano_spanning",
        "illumina_presence",
        "illumina_depth",
        "illumina_paired_end",
        "illumina_soft_clipped",
        "illumina_split_read",
        "nanopore_presence",
        "nanopore_depth",
        "nanopore_soft_clipped",
        "nanopore_split_read",
        "pacbio_presence",
        "pacbio_depth",
        "pacbio_soft_clipped",
        "pacbio_split_read",
        "tenx_presence",
        "tenx_depth",
        "tenx_soft_clipped",
        "tenx_split_read",
        "tenx_linked_read",
        "comments",
        "id"
        ])
    cw.writerows(csvList)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output







@bp.route('/<string:genome>/annotation_data')
def annotation_data(genome):
    """Return server side data for loaded_annotations."""

    # define columns in table:
    columns = [
        ColumnDT(Variants.genome), #0
        ColumnDT(Annotations.user_name),
        ColumnDT(Variants.chromosome),
        ColumnDT(Variants.sv_start),
        ColumnDT(Variants.sv_end),
        ColumnDT(Variants.variant), #5
        ColumnDT(Annotations.bionano_presence), #6
        ColumnDT(Annotations.bionano_depth),
        ColumnDT(Annotations.bionano_partial),
        ColumnDT(Annotations.bionano_spanning), #9
        ColumnDT(Annotations.illumina_presence), #10
        ColumnDT(Annotations.illumina_depth),
        ColumnDT(Annotations.illumina_paired_end),
        ColumnDT(Annotations.illumina_soft_clipped),
        ColumnDT(Annotations.illumina_split_read), #14
        ColumnDT(Annotations.nanopore_presence), #15
        ColumnDT(Annotations.nanopore_depth),
        ColumnDT(Annotations.nanopore_soft_clipped),
        ColumnDT(Annotations.nanopore_split_read), #18
        ColumnDT(Annotations.pacbio_presence), #19
        ColumnDT(Annotations.pacbio_depth),
        ColumnDT(Annotations.pacbio_soft_clipped),
        ColumnDT(Annotations.pacbio_split_read), #22
        ColumnDT(Annotations.tenx_presence), #23
        ColumnDT(Annotations.tenx_depth),
        ColumnDT(Annotations.tenx_soft_clipped),
        ColumnDT(Annotations.tenx_split_read),
        ColumnDT(Annotations.tenx_linked_read), #27
        ColumnDT(Annotations.comments), #28
        # ColumnDT(StaticFiles.technology),
        ColumnDT(Variants.id) #29
    ]

    query = db.session.query(
        Variants.genome,
        Annotations.user_name,
        Variants.chromosome,
        Variants.sv_start,
        Variants.sv_end,
        Variants.variant,
        Annotations.bionano_presence,
        Annotations.bionano_depth,
        Annotations.bionano_partial,
        Annotations.bionano_spanning,
        Annotations.illumina_presence,
        Annotations.illumina_depth,
        Annotations.illumina_paired_end,
        Annotations.illumina_soft_clipped,
        Annotations.illumina_split_read,
        Annotations.nanopore_presence,
        Annotations.nanopore_depth,
        Annotations.nanopore_soft_clipped,
        Annotations.nanopore_split_read,
        Annotations.pacbio_presence,
        Annotations.pacbio_depth,
        Annotations.pacbio_soft_clipped,
        Annotations.pacbio_split_read,
        Annotations.tenx_presence,
        Annotations.tenx_depth,
        Annotations.tenx_soft_clipped,
        Annotations.tenx_split_read,
        Annotations.tenx_linked_read,
        Annotations.comments,
        Variants.id
    ).select_from(
        Variants
    ).outerjoin(
        Annotations, Annotations.variant_id == Variants.id
    ).filter(
        Variants.genome == genome
    )

    params = request.args.to_dict()
    rowTable = DataTables(params, query, columns)
    data = rowTable.output_result()

    return jsonify(data)

#######################################################




#######################################################
@bp.route("/<string:user_name>/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(user_name, id):
    """Update or make a new annotation."""
    
    # Total records for navigating annotations by id:
    total_records = db.session.query(Variants).count()

    # obtain technologies for the genome:
    current_genome = Variants.query.filter(Variants.id == id).all()[0].genome
    all_techs = StaticFiles.query.filter(StaticFiles.genome == current_genome).all()

    # obtain this annotation:
    annotation = Annotations.query.filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()

    # obtain variant info:
    variants = Variants.query.filter(Variants.id == id).all()

    # obtain reference, build, and bed:
    reference = StaticFiles.query.filter(
                StaticFiles.genome == current_genome
            ).first().reference
    reference_build = StaticFiles.query.filter(
                StaticFiles.genome == current_genome
            ).first().reference_build
    bed = StaticFiles.query.filter(
                StaticFiles.genome == current_genome
            ).first().variants
    
    # set to true only if exist; this is for column visibility in datatables:
    bionano,illumina,nanopore,pacbio,tenx = 'false','false','false','false','false'
    illumina_bam_cram,nanopore_bam_cram,pacbio_bam_cram,tenx_bam_cram = '','','',''
    illumina_bai_crai,nanopore_bai_crai,pacbio_bai_crai,tenx_bai_crai = '','','',''
    illumina_tech,nanopore_tech,pacbio_tech,tenx_tech = '','','',''
    for tech in all_techs:
        if tech.technology.lower() == "bionano":
            bionano = 'true'
        elif tech.technology.lower() == "illumina":
            illumina = 'true'
            illumina_bam_cram = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment
            illumina_bai_crai = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment_index
            illumina_tech = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().technology
        elif tech.technology.lower() == "nanopore":
            nanopore = 'true'
            nanopore_bam_cram = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment
            nanopore_bai_crai = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment_index
            nanopore_tech = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().technology
        elif tech.technology.lower() == "pacbio":
            pacbio = 'true'
            pacbio_bam_cram = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment
            pacbio_bai_crai = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment_index
            pacbio_tech = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().technology
        elif tech.technology.lower() == "tenx":
            tenx = 'true'
            tenx_bam_cram = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment
            tenx_bai_crai = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().alignment_index
            tenx_tech = StaticFiles.query.filter(
                StaticFiles.genome == current_genome, 
                StaticFiles.technology == tech.technology
            ).one().technology

    # Initiate annotation form:
    form_detect = DetectForm()

    if request.method == "POST":
        comments = request.form["comments"]

        # illumina:
        if "i_choices" in request.form:
            illumina_presence = request.form["i_choices"]
        else:
            illumina_presence = ""
        if "idepth_choices" in request.form:
            illumina_depth = request.form["idepth_choices"]
        else:
            illumina_depth = ""
        if "ipaired_choices" in request.form:
            illumina_paired_end = request.form["ipaired_choices"]
        else:
            illumina_paired_end = ""
        if "isoft_choices" in request.form:
            illumina_soft_clipped = request.form["isoft_choices"]
        else:
            illumina_soft_clipped = ""
        if "isplit_choices" in request.form:
            illumina_split_read = request.form["isplit_choices"]
        else:
            illumina_split_read = ""

        # nanopore:
        if "n_choices" in request.form:
            nanopore_presence = request.form["n_choices"]
        else:
            nanopore_presence = ""
        if "ndepth_choices" in request.form:
            nanopore_depth = request.form["ndepth_choices"]
        else:
            nanopore_depth = ""
        if "nsoft_choices" in request.form:
            nanopore_soft_clipped = request.form["nsoft_choices"]
        else:
            nanopore_soft_clipped = ""
        if "nsplit_choices" in request.form:
            nanopore_split_read = request.form["nsplit_choices"]
        else:
            nanopore_split_read = ""

        # pacbio:
        if "p_choices" in request.form:
            pacbio_presence = request.form["p_choices"]
        else:
            pacbio_presence = ""
        if "pdepth_choices" in request.form:
            pacbio_depth = request.form["pdepth_choices"]
        else:
            pacbio_depth = ""
        if "psoft_choices" in request.form:
            pacbio_soft_clipped = request.form["psoft_choices"]
        else:
            pacbio_soft_clipped = ""
        if "psplit_choices" in request.form:
            pacbio_split_read = request.form["psplit_choices"]
        else:
            pacbio_split_read = ""
        
        # tenx:
        if "t_choices" in request.form:
            tenx_presence = request.form["t_choices"]
        else:
            tenx_presence = ""
        if "tdepth_choices" in request.form:
            tenx_depth = request.form["tdepth_choices"]
        else:
            tenx_depth = ""
        if "tsoft_choices" in request.form:
            tenx_soft_clipped = request.form["tsoft_choices"]
        else:
            tenx_soft_clipped = ""
        if "tsplit_choices" in request.form:
            tenx_split_read = request.form["tsplit_choices"]
        else:
            tenx_split_read = ""
        if "tlinked_choices" in request.form:
            tenx_linked_read = request.form["tlinked_choices"]
        else:
            tenx_linked_read = ""

        # bionano:
        if "b_choices" in request.form:
            bionano_presence = request.form["b_choices"]
        else:
            bionano_presence = ""
        if "bdepth_choices" in request.form:
            bionano_depth = request.form["bdepth_choices"]
        else:
            bionano_depth = ""
        if "bmols_choices" in request.form:
            bionano_spanning = request.form["bmols_choices"]
        else:
            bionano_spanning = ""
        if "bpartial_choices" in request.form:
            bionano_partial = request.form["bpartial_choices"]
        else:
            bionano_partial = ""
 
        error = None
        
        if error is not None:
            flash("Not saved into annotations table.")
        else:
            # if current user has annotated this variant_id (update):
            q = db.session.query(Annotations)
            q = q.filter(Annotations.variant_id == id)
            q_tmp = q.filter(Annotations.variant_id == id).all()
            user_annotated = q.filter(Annotations.variant_id == id).filter(Annotations.user_name == g.user.username).first()
            if len(q_tmp) > 0 and user_annotated != None:
                if str(user_annotated.user_name) == str(g.user.username):
                    from sqlalchemy import update
                    stmt = update(Annotations).where(Annotations.variant_id == id).where(Annotations.id == user_annotated.id).values(
                        user_id = g.user.id,
                        user_name = g.user.username,
                        comments = comments,
                        genome = current_genome,
                        variant_id = id,
                        bionano_presence = bionano_presence,
                        bionano_depth = bionano_depth,
                        bionano_spanning = bionano_spanning,
                        bionano_partial = bionano_partial,
                        illumina_presence = illumina_presence,
                        illumina_depth = illumina_depth,
                        illumina_paired_end = illumina_paired_end,
                        illumina_soft_clipped = illumina_soft_clipped,
                        illumina_split_read = illumina_split_read,
                        nanopore_presence = nanopore_presence,
                        nanopore_depth = nanopore_depth,
                        nanopore_soft_clipped = nanopore_soft_clipped,
                        nanopore_split_read = nanopore_split_read,
                        pacbio_presence = pacbio_presence,
                        pacbio_depth = pacbio_depth,
                        pacbio_soft_clipped = pacbio_soft_clipped,
                        pacbio_split_read = pacbio_split_read,
                        tenx_presence = tenx_presence,
                        tenx_depth = tenx_depth,
                        tenx_soft_clipped = tenx_soft_clipped,
                        tenx_split_read = tenx_split_read,
                        tenx_linked_read = tenx_linked_read,
                    )
                    db.session.execute(stmt)
                    db.session.commit()
            # if current user or no user has yet to annotate this variant_id:
            else:
                annotation = Annotations(
                user_id = g.user.id,
                user_name = g.user.username,
                comments = comments,
                genome = current_genome,
                variant_id = id,
                bionano_presence = bionano_presence,
                bionano_depth = bionano_depth,
                bionano_spanning = bionano_spanning,
                bionano_partial = bionano_partial,
                illumina_presence = illumina_presence,
                illumina_depth = illumina_depth,
                illumina_paired_end = illumina_paired_end,
                illumina_soft_clipped = illumina_soft_clipped,
                illumina_split_read = illumina_split_read,
                nanopore_presence = nanopore_presence,
                nanopore_depth = nanopore_depth,
                nanopore_soft_clipped = nanopore_soft_clipped,
                nanopore_split_read = nanopore_split_read,
                pacbio_presence = pacbio_presence,
                pacbio_depth = pacbio_depth,
                pacbio_soft_clipped = pacbio_soft_clipped,
                pacbio_split_read = pacbio_split_read,
                tenx_presence = tenx_presence,
                tenx_depth = tenx_depth,
                tenx_soft_clipped = tenx_soft_clipped,
                tenx_split_read = tenx_split_read,
                tenx_linked_read = tenx_linked_read,
                )
                db.session.add(annotation)
                db.session.commit()
            return redirect(url_for("annotations.update", id=id, user_name=g.user.username))

    # Pre-populate the forms if user annotated already:
    check_id_tmp = Annotations.query.filter(Annotations.id == id).all()
    if len(check_id_tmp) > 0:    
        
        # Bionano:
        form_detect.b_choices.choices = [('Yes', 'Yes'), ('No', 'No'), ('Unsure', 'Unsure')]
        b_detects = db.session.query(Annotations.bionano_presence).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(b_detects) > 0:
            form_detect.b_choices.default = str(b_detects[0][0])
        else:
            form_detect.b_choices.default = ""

        form_detect.bdepth_choices.choices = BooleanField(default='unchecked')
        bdepth_detects = db.session.query(Annotations.bionano_depth).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(bdepth_detects) > 0:
            form_detect.bdepth_choices.default = str(bdepth_detects[0][0])
        else:
            form_detect.bdepth_choices.default = ""

        form_detect.bmols_choices.choices = BooleanField(default='unchecked')
        bmols_detects = db.session.query(Annotations.bionano_spanning).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(bmols_detects) > 0:
            form_detect.bmols_choices.default = str(bmols_detects[0][0])
        else:
            form_detect.bmols_choices.default = ""

        form_detect.bpartial_choices.choices = BooleanField(default='unchecked')
        bpartial_detects = db.session.query(Annotations.bionano_partial).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(bpartial_detects) > 0:
            form_detect.bpartial_choices.default = str(bpartial_detects[0][0])
        else:
            form_detect.bpartial_choices.default = ""
        
        # Illumina:
        form_detect.i_choices.choices = [('Yes', 'Yes'), ('No', 'No'), ('Unsure', 'Unsure')]
        i_detects = db.session.query(Annotations.illumina_presence).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(i_detects) > 0:
            form_detect.i_choices.default = str(i_detects[0][0])
        else:
            form_detect.i_choices.default = ""
        
        form_detect.idepth_choices.choices = BooleanField(default='unchecked')
        idepth_detects = db.session.query(Annotations.illumina_depth).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(idepth_detects) > 0:
            form_detect.idepth_choices.default = str(idepth_detects[0][0])
        else:
            form_detect.idepth_choices.default = ""
        
        form_detect.ipaired_choices.choices = BooleanField(default='unchecked')
        ipaired_detects = db.session.query(Annotations.illumina_paired_end).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(ipaired_detects) > 0:
            form_detect.ipaired_choices.default = str(ipaired_detects[0][0])
        else:
            form_detect.ipaired_choices.default = ""
        
        form_detect.isoft_choices.choices = BooleanField(default='unchecked')
        isoft_detects = db.session.query(Annotations.illumina_soft_clipped).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(isoft_detects) > 0:
            form_detect.isoft_choices.default = str(isoft_detects[0][0])
        else:
            form_detect.isoft_choices.default = ""
        
        form_detect.isplit_choices.choices = BooleanField(default='unchecked')
        isplit_detects = db.session.query(Annotations.illumina_split_read).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(isplit_detects) > 0:
            form_detect.isplit_choices.default = str(isplit_detects[0][0])
        else:
            form_detect.isplit_choices.default = ""
        
        # Nanopore:
        form_detect.n_choices.choices = [('Yes', 'Yes'), ('No', 'No'), ('Unsure', 'Unsure')]
        n_detects = db.session.query(Annotations.nanopore_presence).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(n_detects) > 0:
            form_detect.n_choices.default = str(n_detects[0][0])
        else:
            form_detect.n_choices.default = ""
        
        form_detect.ndepth_choices.choices = BooleanField(default='unchecked')
        ndepth_detects = db.session.query(Annotations.nanopore_depth).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(ndepth_detects) > 0:
            form_detect.ndepth_choices.default = str(ndepth_detects[0][0])
        else:
            form_detect.ndepth_choices.default = ""
        
        form_detect.nsoft_choices.choices = BooleanField(default='unchecked')
        nsoft_detects = db.session.query(Annotations.nanopore_soft_clipped).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(nsoft_detects) > 0:
            form_detect.nsoft_choices.default = str(nsoft_detects[0][0])
        else:
            form_detect.nsoft_choices.default = ""
        
        form_detect.nsplit_choices.choices = BooleanField(default='unchecked')
        nsplit_detects = db.session.query(Annotations.nanopore_split_read).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(nsplit_detects) > 0:
            form_detect.nsplit_choices.default = str(nsplit_detects[0][0])
        else:
            form_detect.nsplit_choices.default = ""

        # PacBio:
        form_detect.p_choices.choices = [('Yes', 'Yes'), ('No', 'No'), ('Unsure', 'Unsure')]
        p_detects = db.session.query(Annotations.pacbio_presence).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(p_detects) > 0:
            form_detect.p_choices.default = str(p_detects[0][0])
        else:
            form_detect.p_choices.default = ""
        
        form_detect.pdepth_choices.choices = BooleanField(default='unchecked')
        pdepth_detects = db.session.query(Annotations.pacbio_depth).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(pdepth_detects) > 0:
            form_detect.pdepth_choices.default = str(pdepth_detects[0][0])
        else:
            form_detect.pdepth_choices.default = ""
        
        form_detect.psoft_choices.choices = BooleanField(default='unchecked')
        psoft_detects = db.session.query(Annotations.pacbio_soft_clipped).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(psoft_detects) > 0:
            form_detect.psoft_choices.default = str(psoft_detects[0][0])
        else:
            form_detect.psoft_choices.default = ""
        
        form_detect.psplit_choices.choices = BooleanField(default='unchecked')
        psplit_detects = db.session.query(Annotations.pacbio_split_read).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(psplit_detects) > 0:
            form_detect.psplit_choices.default = str(psplit_detects[0][0])
        else:
            form_detect.psplit_choices.default = ""

        # TenX:
        form_detect.t_choices.choices = [('Yes', 'Yes'), ('No', 'No'), ('Unsure', 'Unsure')]
        t_detects = db.session.query(Annotations.tenx_presence).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(t_detects) > 0:
            form_detect.t_choices.default = str(t_detects[0][0])
        else:
            form_detect.t_choices.default = ""
        
        form_detect.tdepth_choices.choices = BooleanField(default='unchecked')
        tdepth_detects = db.session.query(Annotations.tenx_depth).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(tdepth_detects) > 0:
            form_detect.tdepth_choices.default = str(tdepth_detects[0][0])
        else:
            form_detect.tdepth_choices.default = ""
        
        form_detect.tsoft_choices.choices = BooleanField(default='unchecked')
        tsoft_detects = db.session.query(Annotations.tenx_soft_clipped).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(tsoft_detects) > 0:
            form_detect.tsoft_choices.default = str(tsoft_detects[0][0])
        else:
            form_detect.tsoft_choices.default = ""
        
        form_detect.tsplit_choices.choices = BooleanField(default='unchecked')
        tsplit_detects = db.session.query(Annotations.tenx_split_read).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(tsplit_detects) > 0:
            form_detect.tsplit_choices.default = str(tsplit_detects[0][0])
        else:
            form_detect.tsplit_choices.default = ""

        form_detect.tlinked_choices.choices = BooleanField(default='unchecked')
        tlinked_detects = db.session.query(Annotations.tenx_linked_read).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(tlinked_detects) > 0:
            form_detect.tlinked_choices.default = str(tlinked_detects[0][0])
        else:
            form_detect.tlinked_choices.default = ""

        # comments:
        form_detect.comments.choices = TextAreaField(default='')
        comments_tmp = db.session.query(Annotations.comments).filter(Annotations.variant_id == id, Annotations.user_name == g.user.username).all()
        if len(comments_tmp) > 0:
            form_detect.comments.default = str(comments_tmp[0][0])
        else:
            form_detect.comments.default = ""

        form_detect.process()

    return render_template(
        "annotations/update.html",
        total_records=total_records, 
        form_detect=form_detect, 
        genome=current_genome,
        annotation_id=id,
        annotation=annotation,
        current_user = g.user.username,
        bionano=bionano, 
        illumina=illumina, 
        pacbio=pacbio,
        nanopore=nanopore, 
        tenx=tenx,
        illumina_bam_cram=illumina_bam_cram,
        illumina_bai_crai=illumina_bai_crai,
        nanopore_bam_cram=nanopore_bam_cram,
        nanopore_bai_crai=nanopore_bai_crai,
        pacbio_bam_cram=pacbio_bam_cram,
        pacbio_bai_crai=pacbio_bai_crai,
        tenx_bam_cram=tenx_bam_cram,
        tenx_bai_crai=tenx_bai_crai,
        reference=reference,
        reference_build=reference_build,
        bed=bed,
        illumina_tech=illumina_tech,
        nanopore_tech=nanopore_tech,
        pacbio_tech=pacbio_tech,
        tenx_tech=tenx_tech,
        variants=variants,
        )

#######################################################




#######################################################
@bp.route("/example")
def example():
    """
    Example dataset loaded from /static/data/example
    Post submission disabled for now
    """
    form_detect = DetectForm()
    
    if request.method == "POST":
        comments = request.form["comments"]
        if "i_choices" in request.form:
            illumina_presence = request.form["i_choices"]
        else:
            illumina_presence = ""
        if "idepth_choices" in request.form:
            illumina_depth = request.form["idepth_choices"]
        else:
            illumina_depth = ""
        if "ipaired_choices" in request.form:
            illumina_paired_end = request.form["ipaired_choices"]
        else:
            illumina_paired_end = ""
        if "isoft_choices" in request.form:
            illumina_soft_clipped = request.form["isoft_choices"]
        else:
            illumina_soft_clipped = ""
        if "isplit_choices" in request.form:
            illumina_split_read = request.form["isplit_choices"]
        else:
            illumina_split_read = ""
        error = None

        if error is not None:
            flash(error)
        else:
            print('do nothing.')
            return redirect(url_for("annotation.example"))

    # Processing example setup.csv:
    with open('svcure/static/data/example/setup.csv', 'r') as f:
    # with open('SVCure/static/data/example/setup.csv', 'r') as f:        
        try:
            import csv
            reader = csv.reader(f)
            full_setup_csv = [col for col in reader]
        except IOError:
            flash("A correctly configured setup.csv file is required.")

    example_data = [i for i in full_setup_csv]

    return render_template("annotations/example.html", form_detect=form_detect, example_data=example_data)

#######################################################




#######################################################
@bp.route("/instructions")
def instructions():
    """
    Instructions for using the app
    """
    return render_template("annotations/instructions.html")

#######################################################