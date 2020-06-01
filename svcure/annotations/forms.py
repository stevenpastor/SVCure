from flask import request
from flask_wtf import FlaskForm, Form
from wtforms import RadioField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, InputRequired
from wtforms.fields import StringField
    

from svcure import db
from svcure.annotations.models import Annotations


class DetectForm(Form):

    b_choices = RadioField('Seen in Bionano', choices=[('Yes','Yes'), ('No','No'), ('Unsure','Unsure')], default='Unsure', validators=[DataRequired()])
    bdepth_choices = BooleanField('Molecule Depth', default='unchecked')
    bmols_choices = BooleanField('Molecules Spanning', default='unchecked')
    bpartial_choices = BooleanField('Partial Molecules', default='unchecked')
    i_choices = RadioField('Seen in Illumina', choices=[('Yes','Yes'), ('No','No'), ('Unsure','Unsure')], default='Unsure', validators=[DataRequired()])
    idepth_choices = BooleanField('Read Depth', default='unchecked')
    ipaired_choices = BooleanField('Paired End', default='unchecked')
    isoft_choices = BooleanField('Soft-Clipped', default='unchecked')
    isplit_choices = BooleanField('Split Reads', default='unchecked')
    n_choices = RadioField('Seen in Nanopore', choices=[('Yes','Yes'), ('No','No'), ('Unsure','Unsure')], default='Unsure', validators=[DataRequired()])
    ndepth_choices = BooleanField('Read Depth', default='unchecked')
    nsoft_choices = BooleanField('Soft-Clipped', default='unchecked')
    nsplit_choices = BooleanField('Split Reads', default='unchecked')
    p_choices = RadioField('Seen in PacBio', choices=[('Yes','Yes'), ('No','No'), ('Unsure','Unsure')], default='Unsure', validators=[DataRequired()])
    pdepth_choices = BooleanField('Read Depth', default='unchecked')
    psoft_choices = BooleanField('Soft-Clipped', default='unchecked')
    psplit_choices = BooleanField('Split Reads', default='unchecked')
    t_choices = RadioField('Seen in 10XGenomics', choices=[('Yes','Yes'), ('No','No'), ('Unsure','Unsure')], default='Unsure', validators=[DataRequired()])
    tdepth_choices = BooleanField('Read Depth', default='unchecked')
    tsoft_choices = BooleanField('Soft-Clipped', default='unchecked')
    tsplit_choices = BooleanField('Split Reads', default='unchecked')
    tlinked_choices = BooleanField('Linked Reads', default='unchecked')
    comments = TextAreaField("Comments", default="")
    sv_type = TextAreaField("sv_type", default="")

