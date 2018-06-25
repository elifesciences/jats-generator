from __future__ import print_function
import logging
import time
import os
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
from elifetools import xmlio
from elifearticle import utils as eautils
from elifearticle.article import Article
import ejpcsvparser.parse as parse
from jatsgenerator.conf import raw_config, parse_raw_config
from jatsgenerator import build

LOGGER = logging.getLogger('xml_gen')
HDLR = logging.FileHandler('xml_gen.log')
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
HDLR.setFormatter(FORMATTER)
LOGGER.addHandler(HDLR)
LOGGER.setLevel(logging.INFO)


class ArticleBuildContext(object):
    "keep track of iterators and properties when building an ArticleXML object"
    def __init__(self):
        # sec section counter
        self.sec_count = 0
        # dataset counter
        self.dataro_num = 0
        # corresponding author count, incremented when printing corresp xref
        self.corresp_count = 0
        # author aff count, and dict of author affiliations by index
        self.author_aff_count = 0
        self.author_affs = {}
        # contributor conflict count, incremented when printing contrib xref
        self.conflict_count = 0


class ArticleXML(object):

    def __init__(self, poa_article, jats_config, add_comment=True):
        """
        set the root node
        get the article type from the object passed in to the class
        set default values for items that are boilder plate for this XML
        """
        if not isinstance(poa_article, Article):
            return

        # Set the config
        self.jats_config = jats_config

        # Track the build context
        self.context = ArticleBuildContext()

        # Create the root XML node
        self.root = Element('article')

        if poa_article.article_type:
            self.root.set('article-type', poa_article.article_type)
        self.root.set('xmlns:mml', 'http://www.w3.org/1998/Math/MathML')
        self.root.set('xmlns:xlink', 'http://www.w3.org/1999/xlink')
        self.root.set('dtd-version', '1.1d3')

        # set comment
        if add_comment:
            generated = time.strftime("%Y-%m-%d %H:%M:%S")
            last_commit = eautils.get_last_commit_to_master()
            comment = Comment('generated by ' + str(self.jats_config.get('generator')) +
                              ' at ' + generated +
                              ' from version ' + last_commit)
            self.root.append(comment)

        if poa_article.conflict_default:
            # conf1 is reserved for the default conflict value, so increment now
            self.context.conflict_count += 1

        self.build(self.root, poa_article)

    def build(self, root, poa_article):
        self.set_frontmatter(root, poa_article)
        # self.set_title(self.root, poa_article)
        self.set_backmatter(root, poa_article)

    def set_frontmatter(self, parent, poa_article):
        front = SubElement(parent, 'front')
        self.set_journal_meta(front)
        self.set_article_meta(front, poa_article)
        return front

    def set_backmatter(self, parent, poa_article):
        back = SubElement(parent, 'back')
        info_sec = self.set_section(back, "additional-information")
        info_sec_title = SubElement(info_sec, "title")
        info_sec_title.text = "Additional information"
        if poa_article.has_contributor_conflict() or poa_article.conflict_default:
            build.set_fn_group_competing_interest(info_sec, poa_article)
        if poa_article.ethics:
            build.set_fn_group_ethics_information(info_sec, poa_article)
        if poa_article.datasets or poa_article.data_availability:
            supp_sec = self.set_section(back, "supplementary-material")
            supp_sec_title = SubElement(supp_sec, "title")
            supp_sec_title.text = "Additional Files"
            data_sec = self.set_section(supp_sec, "data-availability")
            self.set_article_datasets(data_sec, poa_article)

    def set_section(self, parent, sec_type):
        self.context.sec_count += 1
        sec = SubElement(parent, "sec")
        sec.set("id", "s" + str(self.context.sec_count))
        sec.set("sec-type", sec_type)
        return sec

    def set_article_meta(self, parent, poa_article):
        article_meta = SubElement(parent, "article-meta")

        # article-id pub-id-type="publisher-id"
        if poa_article.manuscript:
            pub_id_type = "publisher-id"
            article_id = SubElement(article_meta, "article-id")
            article_id.text = str(int(poa_article.manuscript)).zfill(5)
            article_id.set("pub-id-type", pub_id_type)

        # article-id pub-id-type="doi"
        if poa_article.doi:
            pub_id_type = "doi"
            article_id = SubElement(article_meta, "article-id")
            article_id.text = poa_article.doi
            article_id.set("pub-id-type", pub_id_type)

        # article-categories
        build.set_article_categories(article_meta, poa_article)

        build.set_title_group(article_meta, poa_article)

        for contrib_type in self.jats_config.get('contrib_types'):
            self.set_contrib_group(article_meta, poa_article, contrib_type)

        if bool([contrib for contrib in poa_article.contributors if contrib.corresp is True]):
            build.set_author_notes(article_meta, poa_article)

        build.set_pub_date(article_meta, poa_article, "pub")

        build.set_volume(article_meta, poa_article)

        if poa_article.manuscript:
            elocation_id = SubElement(article_meta, "elocation-id")
            elocation_id.text = "e" + str(int(poa_article.manuscript)).zfill(5)

        if poa_article.dates:
            self.set_history(article_meta, poa_article)

        if poa_article.license:
            build.set_permissions(article_meta, poa_article)

        build.set_abstract(article_meta, poa_article)

        # Disabled author keywords from inclusion Oct 2, 2015
        # if poa_article.author_keywords:
        #     build.set_kwd_group_author_keywords(article_meta, poa_article)

        if poa_article.research_organisms:
            build.set_kwd_group_research_organism(article_meta, poa_article)

        if poa_article.funding_awards or poa_article.funding_note:
            build.set_funding_group(article_meta, poa_article)

        return article_meta

    def set_article_datasets(self, parent, poa_article):
        build.set_article_datasets_header(parent)
        build.set_data_availability(parent, poa_article)
        if poa_article.get_datasets("datasets"):
            self.set_major_datasets(parent, poa_article)
        if poa_article.get_datasets("prev_published_datasets"):
            self.set_previously_published_datasets(parent, poa_article)

    def set_major_datasets(self, parent, poa_article):
        p_tag = SubElement(parent, "p")
        p_tag.text = "The following datasets were generated:"
        p_tag = SubElement(parent, "p")
        specific_use = "isSupplementedBy"
        # Datasets
        for dataset in poa_article.get_datasets("datasets"):
            self.context.dataro_num += 1
            build.set_dataset(p_tag, dataset, self.context.dataro_num, specific_use)

    def set_previously_published_datasets(self, parent, poa_article):
        p_tag = SubElement(parent, "p")
        p_tag.text = "The following previously published datasets were used:"
        p_tag = SubElement(parent, "p")
        specific_use = "references"
        # Datasets
        for dataset in poa_article.get_datasets("prev_published_datasets"):
            self.context.dataro_num += 1
            build.set_dataset(p_tag, dataset, self.context.dataro_num, specific_use)

    def set_journal_title_group(self, parent):
        """
        take boiler plate values from the init of the class
        """

        # journal-title-group
        journal_title_group = SubElement(parent, "journal-title-group")

        # journal-title
        journal_title = SubElement(journal_title_group, "journal-title")
        journal_title.text = self.jats_config.get('journal_title')

    def set_journal_meta(self, parent):
        """
        take boiler plate values from the init of the class
        """
        journal_meta = SubElement(parent, "journal-meta")

        # journal-id
        for journal_id_type in self.jats_config.get('journal_id_types'):
            # concatenate the config name to look for the value
            config_name = "journal_id_" + journal_id_type
            journal_id_value = self.jats_config.get(config_name)
            if journal_id_value:
                journal_id = SubElement(journal_meta, "journal-id")
                journal_id.set("journal-id-type", journal_id_type)
                journal_id.text = journal_id_value
        #
        self.set_journal_title_group(journal_meta)

        # title-group
        issn = SubElement(journal_meta, "issn")
        issn.text = self.jats_config.get('journal_issn')
        issn.set("publication-format", "electronic")

        # publisher
        publisher = SubElement(journal_meta, "publisher")
        publisher_name = SubElement(publisher, "publisher-name")
        publisher_name.text = self.jats_config.get('publisher_name')

    def get_aff_id(self, affiliation):
        """
        For each unique author affiliation, assign it a unique id value
        and keep track of all the affs in a dict
        This can be assembled by processing each author aff in succession
        Return the new or existing aff_id dict index
        """
        aff_id = None

        for key, value in self.context.author_affs.items():
            if build.compare_aff(affiliation, value):
                aff_id = key
        if not aff_id:
            self.context.author_aff_count += 1
            aff_id = self.context.author_aff_count
            self.context.author_affs[aff_id] = affiliation

        return aff_id

    def set_contrib_group(self, parent, poa_article, contrib_type=None):
        # If contrib_type is None, all contributors will be added regardless of their type
        contrib_group = SubElement(parent, "contrib-group")
        if contrib_type == "editor":
            contrib_group.set("content-type", "section")

        for contributor in poa_article.contributors:
            if contrib_type:
                # Filter by contrib_type if supplied
                if contributor.contrib_type != contrib_type:
                    continue

            contrib_tag = SubElement(contrib_group, "contrib")

            contrib_tag.set("contrib-type", contributor.contrib_type)
            if contributor.corresp is True:
                contrib_tag.set("corresp", "yes")
            if contributor.equal_contrib is True:
                contrib_tag.set("equal_contrib", "yes")
            if contributor.auth_id:
                contrib_tag.set("id", "author-" + str(contributor.auth_id))

            if contributor.collab:
                collab_tag = SubElement(contrib_tag, "collab")
                collab_tag.text = contributor.collab
            else:
                build.set_name(contrib_tag, contributor)

            if contrib_type == "editor":
                role_tag = SubElement(contrib_tag, "role")
                role_tag.text = "Reviewing editor"

            if contributor.orcid:
                orcid_tag = SubElement(contrib_tag, "contrib-id")
                orcid_tag.set("contrib-id-type", "orcid")
                orcid_tag.text = "http://orcid.org/" + contributor.orcid

            for affiliation in contributor.affiliations:
                if contrib_type != "editor":
                    aff_id = self.get_aff_id(affiliation)
                    rid = "aff" + str(aff_id)
                    xref_tag = SubElement(contrib_tag, "xref")
                    xref_tag.set("ref-type", "aff")
                    xref_tag.set("rid", rid)
                    xref_tag.text = str(aff_id)
                else:
                    # For editors add an inline aff tag
                    build.set_aff(contrib_tag, affiliation, contrib_type, aff_id=None)

            # Corresponding author xref tag logic
            if contributor.corresp is True:
                self.context.corresp_count += 1
                rid = "cor" + str(self.context.corresp_count)
                xref_tag = SubElement(contrib_tag, "xref")
                xref_tag.set("ref-type", "corresp")
                xref_tag.set("rid", rid)
                xref_tag.text = "*"

            # Funding award group xref tags
            for par_id in build.get_contrib_par_ids(poa_article, contributor.auth_id):
                xref_tag = SubElement(contrib_tag, "xref")
                xref_tag.set("ref-type", "other")
                xref_tag.set("rid", par_id)

            # Contributor conflict xref tag logic
            if contributor.conflict:
                self.context.conflict_count += 1
                rid = "conf" + str(self.context.conflict_count)
            elif poa_article.conflict_default:
                rid = "conf1"
            else:
                rid = None

            # Contrib conflict xref
            if contrib_type != "editor":
                if rid:
                    xref_tag = SubElement(contrib_tag, "xref")
                    xref_tag.set("ref-type", "fn")
                    xref_tag.set("rid", rid)

        # Add the aff tags
        if contrib_type != "editor":
            for key, value in self.context.author_affs.items():
                aff_id = "aff" + str(key)
                build.set_aff(contrib_group, value, contrib_type, aff_id)

    def set_history(self, parent, poa_article):
        history = SubElement(parent, "history")

        for date_type in self.jats_config.get('history_date_types'):
            date = poa_article.get_date(date_type)
            if date:
                build.set_date(history, poa_article, date_type)

    def output_xml(self, pretty=False, indent=""):
        public_id = ('-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange ' +
                     'DTD v1.1d3 20150301//EN')
        system_id = 'JATS-archivearticle1.dtd'
        encoding = 'utf-8'
        qualified_name = "article"

        doctype = xmlio.ElifeDocumentType(qualified_name)
        doctype._identified_mixin_init(public_id, system_id)

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)
        if doctype:
            reparsed.insertBefore(doctype, reparsed.documentElement)

        if pretty is True:
            return reparsed.toprettyxml(indent, encoding=encoding)
        return reparsed.toxml(encoding=encoding)


def write_xml_to_disk(article_xml, filename, output_dir=None):
    filename_path = filename
    if output_dir:
        filename_path = output_dir + os.sep + filename
    with open(filename_path, "wb") as open_file:
        open_file.write(article_xml.output_xml())


def build_article_from_csv(article_id, jats_config=None):
    "build article objects populated with csv data"
    if not jats_config:
        jats_config = parse_raw_config(raw_config(None))
    article, error_count, error_messages = parse.build_article(article_id)
    if article:
        return article
    else:
        LOGGER.warning("the following article did not have enough components and " +
                       "xml was not generated %s", article_id)
        LOGGER.warning("warning count was %s", error_count)
        if error_messages:
            LOGGER.warning(", ".join(error_messages))
        return False


def build_xml(article_id, article=None, jats_config=None, add_comment=True):
    "generate xml from an article object"
    if not jats_config:
        jats_config = parse_raw_config(raw_config(None))

    if not article:
        article = build_article_from_csv(article_id, jats_config)
        if not hasattr(article, 'manuscript'):
            LOGGER.info("could not build article for %s", article_id)
            return None

    article_xml = ArticleXML(article, jats_config, add_comment)
    if hasattr(article_xml, 'root'):
        LOGGER.info("generated xml for %s", article_id)
        return article_xml
    return None


def build_xml_to_disk(article_id, article=None, jats_config=None, add_comment=True):
    "generate xml from an article object and write to disk"
    if not jats_config:
        jats_config = parse_raw_config(raw_config(None))
    if not article:
        article = build_article_from_csv(article_id, jats_config)
    article_xml = build_xml(article_id, article, jats_config, add_comment)
    if article_xml and hasattr(article_xml, 'root'):
        filename = jats_config.get("xml_filename_pattern").format(
            manuscript=article.manuscript)
        try:
            output_dir = jats_config.get("target_output_dir")
            write_xml_to_disk(article_xml, filename, output_dir)
            LOGGER.info("xml written for %s", article_id)
            print("written " + str(article_id))
            return True
        except IOError:
            LOGGER.error("could not write xml for %s", article_id)
            return False
    LOGGER.error("could not generate xml to disk for %s", article_id)
    return False
