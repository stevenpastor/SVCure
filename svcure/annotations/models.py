from flask import url_for

from svcure import db
from svcure.auth.models import User


class StaticFiles(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    genome = db.Column(db.String, nullable=False)
    alignment = db.Column(db.String, nullable=False, unique=True)
    alignment_index = db.Column(db.String, nullable=False, unique=True)
    reference = db.Column(db.String, nullable=False)
    reference_build = db.Column(db.String, nullable=False)
    variants = db.Column(db.String, nullable=False)
    technology = db.Column(db.String, nullable=False)

    # User object backed by user_id
    # lazy="joined" means the user is returned with the post in one query
    # author = db.relationship(User, lazy="joined", backref="staticfiles")

    # @property
    # def update_url(self):
    #     return url_for("annotations.update", id=self.id)

    # @property
    # def delete_url(self):
    #     return url_for("annotations.delete", id=self.id)

    # @property
    # def load_annotations(self):
    #     return url_for("annotations.load_annotations", id=self.id)


class Genomes(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    genome = db.Column(db.String, nullable=False, unique=True)


class Variants(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    genome = db.Column(db.ForeignKey(StaticFiles.genome), nullable=False)
    chromosome = db.Column(db.String, nullable=False)
    sv_start = db.Column(db.Integer, nullable=False)
    sv_end = db.Column(db.Integer, nullable=False)
    variant = db.Column(db.String, nullable=False)
    technology = db.Column(db.String, nullable=False)

    genomes = db.relationship("StaticFiles", foreign_keys=[genome])

    __table_args__ = (db.UniqueConstraint('genome', 
                                          'chromosome', 'sv_start', 'sv_end', 
                                          'variant', 'technology',
                                          name='_genome_chr_start_end_variant_tech'),
                     )


class Annotations(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    user_name = db.Column(db.ForeignKey(User.username), nullable=False)
    genome = db.Column(db.ForeignKey(Variants.genome), nullable=False)
    variant_id = db.Column(db.ForeignKey(Variants.id), nullable=False)
    bionano_presence = db.Column(db.String, nullable=True)
    bionano_depth = db.Column(db.String, nullable=True)
    bionano_spanning = db.Column(db.String, nullable=True)
    bionano_partial = db.Column(db.String, nullable=True)
    illumina_presence = db.Column(db.String, nullable=True)
    illumina_depth = db.Column(db.String, nullable=True)
    illumina_paired_end = db.Column(db.String, nullable=True)
    illumina_soft_clipped = db.Column(db.String, nullable=True)
    illumina_split_read = db.Column(db.String, nullable=True)
    nanopore_presence = db.Column(db.String, nullable=True)
    nanopore_depth = db.Column(db.String, nullable=True)
    nanopore_soft_clipped = db.Column(db.String, nullable=True)
    nanopore_split_read = db.Column(db.String, nullable=True)
    pacbio_presence = db.Column(db.String, nullable=True)
    pacbio_depth = db.Column(db.String, nullable=True)
    pacbio_soft_clipped = db.Column(db.String, nullable=True)
    pacbio_split_read = db.Column(db.String, nullable=True)
    tenx_presence = db.Column(db.String, nullable=True)
    tenx_depth = db.Column(db.String, nullable=True)
    tenx_soft_clipped = db.Column(db.String, nullable=True)
    tenx_split_read = db.Column(db.String, nullable=True)
    tenx_linked_read = db.Column(db.String, nullable=True)
    comments = db.Column(db.String, nullable=True)
    technology = db.Column(db.ForeignKey(StaticFiles.technology), nullable=True)

    author = db.relationship("User", foreign_keys=[user_id])
    author_name = db.relationship("User", foreign_keys=[user_name])
    genomes = db.relationship("Variants", foreign_keys=[genome])
    variants = db.relationship("Variants", foreign_keys=[variant_id])
    techs = db.relationship("StaticFiles", foreign_keys=[technology])

    __table_args__ = (db.UniqueConstraint('user_id', 'user_name', 
    # __table_args__ = (db.UniqueConstraint('user_id', 'user_name', 'static_file_id', 
                                          'genome', 
                                        #   'chromosome', 'sv_start', 'sv_end', 
                                          'variant_id', 
                                          'technology', name='_user_id_s'),
                                        #   'technology', name='_user_id_static_file_id'),
                     )
    # __table_args__ = (db.UniqueConstraint('id' ,
    #                                       'genome', 
    #                                       name='_id_genome'),
    #                  )

