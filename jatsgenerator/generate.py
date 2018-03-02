from __future__ import print_function
import logging
import time
import os
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
from jatsgenerator.conf import config, parse_raw_config
from elifetools import utils as etoolsutils
from elifetools import xmlio
from elifearticle import utils as eautils
import ejpcsvparser.parse as parse
import ejpcsvparser.csv_data as data
import ejpcsvparser.settings as settings


logger = logging.getLogger('xml_gen')
hdlr = logging.FileHandler('xml_gen.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class ArticleXML(object):

    def __init__(self, poa_article, jats_config, add_comment=True):
        """
        set the root node
        get the article type from the object passed in to the class
        set default values for items that are boilder plate for this XML
        """
        # Set the config
        self.jats_config = jats_config
        # Create the root XML node
        self.root = Element('article')

        self.root.set('article-type', poa_article.article_type)
        self.root.set('xmlns:mml', 'http://www.w3.org/1998/Math/MathML')
        self.root.set('xmlns:xlink', 'http://www.w3.org/1999/xlink')
        self.root.set('dtd-version', '1.1d3')

        # set comment
        if add_comment:
            self.generated = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_commit = eautils.get_last_commit_to_master()
            self.comment = Comment('generated by ' + str(self.jats_config.get('generator')) +
                                   ' at ' + self.generated +
                                   ' from version ' + self.last_commit)
            self.root.append(self.comment)

        # contributor conflict count, incremented when printing contrib xref
        self.conflict_count = 0
        if poa_article.conflict_default:
            # conf1 is reserved for the default conflict value, so increment now
            self.conflict_count += 1

        # sec section counter
        self.sec_count = 0

        # corresponding author count, incremented when printing corresp xref
        self.corresp_count = 0

        # author aff count, and dict of author affiliations by index
        self.author_aff_count = 0
        self.author_affs = {}

        self.build(self.root, poa_article)

    def build(self, root, poa_article):
        self.set_frontmatter(self.root, poa_article)
        # self.set_title(self.root, poa_article)
        self.set_backmatter(self.root, poa_article)

    def set_frontmatter(self, parent, poa_article):
        self.front = SubElement(parent, 'front')
        self.set_journal_meta(self.front)
        self.set_article_meta(self.front, poa_article)

    def set_backmatter(self, parent, poa_article):
        self.back = SubElement(parent, 'back')
        self.sec = self.set_section(self.back, "additional-information")
        self.sec_title = SubElement(self.sec, "title")
        self.sec_title.text = "Additional information"
        if poa_article.has_contributor_conflict() or poa_article.conflict_default:
            self.set_fn_group_competing_interest(self.sec, poa_article)
        if len(poa_article.ethics) > 0:
            self.set_fn_group_ethics_information(self.sec, poa_article)
        if len(poa_article.datasets) > 0:
            self.sec = self.set_section(self.back, "supplementary-material")
            self.sec_title = SubElement(self.sec, "title")
            self.sec_title.text = "Additional Files"
            self.sec = self.set_section(self.sec, "datasets")
            self.set_article_datasets(self.sec, poa_article)

    def set_section(self, parent, sec_type):
        self.sec_count = self.sec_count + 1
        self.sec = SubElement(parent, "sec")
        self.sec.set("id", "s" + str(self.sec_count))
        self.sec.set("sec-type", sec_type)
        return self.sec

    def set_fn_group_competing_interest(self, parent, poa_article):
        self.competing_interest = SubElement(parent, "fn-group")
        self.competing_interest.set("content-type", "competing-interest")
        title = SubElement(self.competing_interest, "title")
        title.text = "Competing interest"

        # Check if we are supplied a conflict default statement and set count accordingly
        if poa_article.conflict_default:
            conflict_count = 1
        else:
            conflict_count = 0

        for contributor in poa_article.contributors:
            if contributor.conflict:
                for conflict in  contributor.conflict:
                    conf_id = "conf" + str(conflict_count + 1)
                    fn_tag = SubElement(self.competing_interest, "fn")
                    fn_tag.set("fn-type", "conflict")
                    fn_tag.set("id", conf_id)
                    p_tag = SubElement(fn_tag, "p")
                    p_tag.text = contributor.given_name + " " + contributor.surname + ", "
                    p_tag.text = p_tag.text + conflict + "."
                    # increment
                    conflict_count = conflict_count + 1
        if poa_article.conflict_default:
            # default for contributors with no conflicts
            if conflict_count > 1:
                # Change the default conflict text
                conflict_text = "The other authors declare that no competing interests exist."
            else:
                conflict_text = poa_article.conflict_default
            conf_id = "conf1"
            fn_tag = SubElement(self.competing_interest, "fn")
            fn_tag.set("fn-type", "conflict")
            fn_tag.set("id", conf_id)
            p_tag = SubElement(fn_tag, "p")
            p_tag.text = conflict_text
            conflict_count = conflict_count + 1

    def set_fn_group_ethics_information(self, parent, poa_article):
        self.competing_interest = SubElement(parent, "fn-group")
        self.competing_interest.set("content-type", "ethics-information")
        title = SubElement(self.competing_interest, "title")
        title.text = "Ethics"

        for ethic in poa_article.ethics:
            fn_tag = SubElement(self.competing_interest, "fn")
            fn_tag.set("fn-type", "other")
            p_tag = SubElement(fn_tag, "p")
            p_tag.text = ethic

    def set_article_meta(self, parent, poa_article):
        self.article_meta = SubElement(parent, "article-meta")

        # article-id pub-id-type="publisher-id"
        if poa_article.manuscript:
            pub_id_type = "publisher-id"
            self.article_id = SubElement(self.article_meta, "article-id")
            self.article_id.text = str(int(poa_article.manuscript)).zfill(5)
            self.article_id.set("pub-id-type", pub_id_type)

        # article-id pub-id-type="doi"
        if poa_article.doi:
            pub_id_type = "doi"
            self.article_id = SubElement(self.article_meta, "article-id")
            self.article_id.text = poa_article.doi
            self.article_id.set("pub-id-type", pub_id_type)

        # article-categories
        self.set_article_categories(self.article_meta, poa_article)

        self.set_title_group(self.article_meta, poa_article)

        for contrib_type in self.jats_config.get('contrib_types'):
            self.set_contrib_group(self.article_meta, poa_article, contrib_type)

        if bool([contrib for contrib in poa_article.contributors if contrib.corresp is True]):
            self.set_author_notes(self.article_meta, poa_article)

        self.set_pub_date(self.article_meta, poa_article, "pub")

        self.set_volume(self.article_meta, poa_article)

        if poa_article.manuscript:
            self.elocation_id = SubElement(self.article_meta, "elocation-id")
            self.elocation_id.text = "e" + str(int(poa_article.manuscript)).zfill(5)

        if poa_article.dates:
            self.set_history(self.article_meta, poa_article)

        if poa_article.license:
            self.set_permissions(self.article_meta, poa_article)

        self.set_abstract(self.article_meta, poa_article)


        # Disabled author keywords from inclusion Oct 2, 2015
        """
        if len(poa_article.author_keywords) > 0:
            self.set_kwd_group_author_keywords(self.article_meta, poa_article)
        """

        if len(poa_article.research_organisms) > 0:
            self.set_kwd_group_research_organism(self.article_meta, poa_article)

        if len(poa_article.funding_awards) > 0 or poa_article.funding_note:
            self.set_funding_group(self.article_meta, poa_article)

    def set_article_datasets(self, parent, poa_article):
        self.dataro_num = 0
        self.set_article_datasets_header(parent)
        if len(poa_article.get_datasets("datasets")) > 0:
            self.set_major_datasets(parent, poa_article)
        if len(poa_article.get_datasets("prev_published_datasets")) > 0:
            self.set_previously_published_datasets(parent, poa_article)

    def set_article_datasets_header(self, parent):
        self.sec_title = SubElement(parent, "title")
        self.sec_title.text = "Major datasets"
        self.p_tag = SubElement(parent, "p")

    def set_major_datasets(self, parent, poa_article):
        self.p_tag = SubElement(parent, "p")
        self.p_tag.text = "The following datasets were generated:"
        self.p_tag = SubElement(parent, "p")
        # Datasets
        for dataset in poa_article.get_datasets("datasets"):
            self.dataro_num = self.dataro_num + 1
            self.set_dataset(self.p_tag, dataset, self.dataro_num)
        return parent

    def set_previously_published_datasets(self, parent, poa_article):
        self.p_tag = SubElement(parent, "p")
        self.p_tag.text = "The following previously published datasets were used:"
        self.p_tag = SubElement(parent, "p")
        # Datasets
        for dataset in poa_article.get_datasets("prev_published_datasets"):
            self.dataro_num = self.dataro_num + 1
            self.set_dataset(self.p_tag, dataset, self.dataro_num)
        return parent

    def set_dataset(self, parent, dataset, dataro_num):
        self.related_object = SubElement(parent, "related-object")
        self.related_object.set('id', 'dataro' + str(dataro_num))
        self.related_object.set('content-type', 'generated-dataset')

        if dataset.source_id:
            self.related_object.set('source-id-type', 'uri')
            self.related_object.set('source-id', dataset.source_id)

        if len(dataset.authors) > 0:
            for author in dataset.authors:
                self.collab = SubElement(self.related_object, "collab")
                self.collab.text = author
                self.collab.tail = ", "

        dataset_tags = []

        if dataset.year:
            self.year = Element("year")
            self.year.text = dataset.year
            dataset_tags.append(self.year)

        if dataset.title:
            self.source = Element("source")
            self.source.text = dataset.title
            dataset_tags.append(self.source)

        if dataset.source_id:
            self.ext_link = Element("ext-link")
            self.ext_link.text = dataset.source_id
            self.ext_link.set("ext-link-type", "uri")
            self.ext_link.set("xlink:href", dataset.source_id)
            dataset_tags.append(self.ext_link)

        if dataset.license_info:
            self.comment = Element("comment")
            self.comment.text = dataset.license_info
            dataset_tags.append(self.comment)

        # Add tags with <x>,</x> in between them
        for i, tag in enumerate(dataset_tags):
            self.related_object.append(tag)
            if i < len(dataset_tags) - 1:
                self.x_tag = Element("x")
                self.x_tag.text = ","
                self.x_tag.tail = " "
                self.related_object.append(self.x_tag)


    def set_title_group(self, parent, poa_article):
        """
        Allows the addition of XML tags
        """
        root_tag_name = 'title-group'
        tag_name = 'article-title'
        root_xml_element = Element(root_tag_name)
        # Escape any unescaped ampersands
        title = etoolsutils.escape_ampersand(poa_article.title)

        # XML
        tagged_string = '<' + tag_name + '>' + title + '</' + tag_name + '>'
        reparsed = minidom.parseString(tagged_string.encode('utf8'))

        root_xml_element = xmlio.append_minidom_xml_to_elementtree_xml(
            root_xml_element, reparsed
            )

        parent.append(root_xml_element)

    def set_journal_title_group(self, parent):
        """
        take boiler plate values from the init of the class
        """

        # journal-title-group
        self.journal_title_group = SubElement(parent, "journal-title-group")

        # journal-title
        self.journal_title = SubElement(self.journal_title_group, "journal-title")
        self.journal_title.text = self.jats_config.get('journal_title')

    def set_journal_meta(self, parent):
        """
        take boiler plate values from the init of the class
        """
        self.journal_meta = SubElement(parent, "journal-meta")

        # journal-id
        for journal_id_type in self.jats_config.get('journal_id_types'):
            # concatenate the config name to look for the value
            config_name = "journal_id_" + journal_id_type
            journal_id_value = self.jats_config.get(config_name)
            if journal_id_value:
                journal_id = SubElement(self.journal_meta, "journal-id")
                journal_id.set("journal-id-type", journal_id_type)
                journal_id.text = journal_id_value
        #
        self.set_journal_title_group(self.journal_meta)

        # title-group
        self.issn = SubElement(self.journal_meta, "issn")
        self.issn.text = self.jats_config.get('journal_issn')
        self.issn.set("publication-format", "electronic")

        # publisher
        self.publisher = SubElement(self.journal_meta, "publisher")
        self.publisher_name = SubElement(self.publisher, "publisher-name")
        self.publisher_name.text = self.jats_config.get('publisher_name')

    def set_license(self, parent, poa_article):
        self.license = SubElement(parent, "license")

        self.license.set("xlink:href", poa_article.license.href)

        self.license_p = SubElement(self.license, "license-p")
        self.license_p.text = poa_article.license.paragraph1

        ext_link = SubElement(self.license_p, "ext-link")
        ext_link.set("ext-link-type", "uri")
        ext_link.set("xlink:href", poa_article.license.href)
        ext_link.text = poa_article.license.name
        ext_link.tail = poa_article.license.paragraph2

    def set_copyright(self, parent, poa_article):
        # Count authors (non-editors)
        non_editor = []
        for c in poa_article.contributors:
            if c.contrib_type != "editor":
                non_editor.append(c)

        if len(non_editor) > 2:
            contributor = non_editor[0]
            copyright_holder = contributor.surname + " et al"
        elif len(non_editor) == 2:
            contributor1 = non_editor[0]
            contributor2 = non_editor[1]
            copyright_holder = contributor1.surname + " & " + contributor2.surname
        elif len(non_editor) == 1:
            contributor = non_editor[0]
            copyright_holder = contributor.surname
        else:
            copyright_holder = ""

        # copyright-statement
        copyright_year = ""
        date = poa_article.get_date("license")
        if not date:
            # if no license date specified, use the article accepted date
            date = poa_article.get_date("accepted")
        if date:
            copyright_year = date.date.tm_year

        copyright_statement = u'\u00a9 ' + str(copyright_year) + ", " + copyright_holder
        self.copyright_statement = SubElement(parent, "copyright-statement")
        self.copyright_statement.text = copyright_statement

        # copyright-year
        self.copyright_year = SubElement(parent, "copyright-year")
        self.copyright_year.text = str(copyright_year)

        # copyright-holder
        self.copyright_holder = SubElement(parent, "copyright-holder")
        self.copyright_holder.text = copyright_holder

    def set_permissions(self, parent, poa_article):
        self.permissions = SubElement(parent, "permissions")
        if poa_article.license.copyright is True:
            self.set_copyright(self.permissions, poa_article)
        self.set_license(self.permissions, poa_article)

    def set_abstract(self, parent, poa_article):
        """
        Allows the addition of XML tags
        """
        root_tag_name = 'abstract'
        tag_name = 'p'
        root_xml_element = Element(root_tag_name)
        # Escape any unescaped ampersands
        abstract = etoolsutils.escape_ampersand(poa_article.abstract)

        # XML
        tagged_string = '<' + tag_name + '>' + abstract + '</' + tag_name + '>'
        reparsed = minidom.parseString(tagged_string.encode('utf8'))

        root_xml_element = xmlio.append_minidom_xml_to_elementtree_xml(
            root_xml_element, reparsed
            )

        parent.append(root_xml_element)

    def get_aff_id(self, affiliation):
        """
        For each unique author affiliation, assign it a unique id value
        and keep track of all the affs in a dict
        This can be assembled by processing each author aff in succession
        Return the new or existing aff_id dict index
        """
        aff_id = None

        for key, value in self.author_affs.items():
            if self.compare_aff(affiliation, value):
                aff_id = key
        if not aff_id:
            self.author_aff_count += 1
            aff_id = self.author_aff_count
            self.author_affs[aff_id] = affiliation

        return aff_id

    def get_contrib_par_ids(self, poa_article, auth_id):
        """
        In order to set xref tags for authors that link to funding award id
        traverse the article data to match values
        """
        par_ids = []
        for index, award in enumerate(poa_article.funding_awards):
            par_id = "par-" + str(index + 1)
            for contributor in award.principal_award_recipients:
                if contributor.auth_id == auth_id:
                    par_ids.append(par_id)
        return par_ids

    def compare_aff(self, aff1, aff2):
        # Compare two affiliations by comparing the object attributes
        attrs = ['city', 'country', 'department', 'institution']
        for attr in attrs:
            if (getattr(aff1, attr) and getattr(aff2, attr) and
                    getattr(aff1, attr) != getattr(aff2, attr)):
                return False
        return True

    def set_contrib_group(self, parent, poa_article, contrib_type=None):
        # If contrib_type is None, all contributors will be added regardless of their type
        self.contrib_group = SubElement(parent, "contrib-group")
        if contrib_type == "editor":
            self.contrib_group.set("content-type", "section")

        for contributor in poa_article.contributors:
            if contrib_type:
                # Filter by contrib_type if supplied
                if contributor.contrib_type != contrib_type:
                    continue

            self.contrib = SubElement(self.contrib_group, "contrib")

            self.contrib.set("contrib-type", contributor.contrib_type)
            if contributor.corresp is True:
                self.contrib.set("corresp", "yes")
            if contributor.equal_contrib is True:
                self.contrib.set("equal_contrib", "yes")
            if contributor.auth_id:
                self.contrib.set("id", "author-" + str(contributor.auth_id))

            if contributor.collab:
                self.collab = SubElement(self.contrib, "collab")
                self.collab.text = contributor.collab
            else:
                self.set_name(self.contrib, contributor)

            if contrib_type == "editor":
                self.role = SubElement(self.contrib, "role")
                self.role.text = "Reviewing editor"

            if contributor.orcid:
                self.orcid = SubElement(self.contrib, "contrib-id")
                self.orcid.set("contrib-id-type", "orcid")
                self.orcid.text = "http://orcid.org/" + contributor.orcid

            for affiliation in contributor.affiliations:
                if contrib_type != "editor":
                    aff_id = self.get_aff_id(affiliation)
                    rid = "aff" + str(aff_id)
                    self.xref = SubElement(self.contrib, "xref")
                    self.xref.set("ref-type", "aff")
                    self.xref.set("rid", rid)
                    self.xref.text = str(aff_id)
                else:
                    # For editors add an inline aff tag
                    self.set_aff(self.contrib, affiliation, contrib_type, aff_id=None)

            # Corresponding author xref tag logic
            if contributor.corresp is True:
                self.corresp_count += 1
                rid = "cor" + str(self.corresp_count)
                self.xref = SubElement(self.contrib, "xref")
                self.xref.set("ref-type", "corresp")
                self.xref.set("rid", rid)
                self.xref.text = "*"

            # Funding award group xref tags
            for par_id in self.get_contrib_par_ids(poa_article, contributor.auth_id):
                self.xref = SubElement(self.contrib, "xref")
                self.xref.set("ref-type", "other")
                self.xref.set("rid", par_id)

            # Contributor conflict xref tag logic
            if contributor.conflict:
                rid = "conf" + str(self.conflict_count + 1)
                self.conflict_count += 1
            elif poa_article.conflict_default:
                rid = "conf1"
            else:
                rid = None

            # Contrib conflict xref
            if contrib_type != "editor":
                if rid:
                    self.xref = SubElement(self.contrib, "xref")
                    self.xref.set("ref-type", "fn")
                    self.xref.set("rid", rid)

        # Add the aff tags
        if contrib_type != "editor":
            for key, value in self.author_affs.items():
                aff_id = "aff" + str(key)
                self.set_aff(self.contrib_group, value, contrib_type, aff_id)

    def set_name(self, parent, contributor):
        self.name = SubElement(parent, "name")
        self.surname = SubElement(self.name, "surname")
        self.surname.text = contributor.surname
        self.given_name = SubElement(self.name, "given-names")
        self.given_name.text = contributor.given_name

    def set_aff(self, parent, affiliation, contrib_type, aff_id=None):
        self.aff = SubElement(parent, "aff")

        if aff_id:
            self.aff.set("id", aff_id)

        if contrib_type != "editor":
            if affiliation.department:
                self.department = SubElement(self.aff, "institution")
                self.department.set("content-type", "dept")
                self.department.text = affiliation.department
                self.department.tail = ", "

        if affiliation.institution:
            self.institution = SubElement(self.aff, "institution")
            self.institution.text = affiliation.institution
            self.institution.tail = ", "

        if affiliation.city:
            self.addline = SubElement(self.aff, "addr-line")
            self.city = SubElement(self.addline, "named-content")
            self.city.set("content-type", "city")
            self.city.text = affiliation.city
            self.addline.tail = ", "

        if affiliation.country:
            self.country = SubElement(self.aff, "country")
            self.country.text = affiliation.country

        if affiliation.phone:
            self.phone = SubElement(self.aff, "phone")
            self.phone.text = affiliation.phone

        if affiliation.fax:
            self.fax = SubElement(self.aff, "fax")
            self.fax.text = affiliation.fax

    def do_display_channel(self, poa_article):
        "decide whether to add a display-channel"
        if (poa_article.get_display_channel() and
                poa_article.get_display_channel().strip() != ''):
            return True
        return False

    def do_subject_heading(self, poa_article):
        "decide whether to add subject headings from article_categories"
        if poa_article.article_categories:
            for heading in poa_article.article_categories:
                if heading and heading.strip() != '':
                    return True
        return False

    def do_article_categories(self, poa_article):
        "check whether we will add any article-categories values"
        return bool(self.do_display_channel(poa_article) or self.do_subject_heading(poa_article))

    def set_article_categories(self, parent, poa_article):
        # article-categories
        if self.do_article_categories(poa_article):
            self.article_categories = SubElement(parent, "article-categories")

            if self.do_display_channel(poa_article):
                # subj-group subj-group-type="display-channel"
                subj_group = SubElement(self.article_categories, "subj-group")
                subj_group.set("subj-group-type", "display-channel")
                subject = SubElement(subj_group, "subject")
                subject.text = poa_article.get_display_channel()

            if self.do_subject_heading(poa_article):
                for article_category in poa_article.article_categories:
                    # subj-group subj-group-type="heading"
                    if article_category and article_category.rstrip().lstrip() != '':
                        subj_group = SubElement(self.article_categories, "subj-group")
                        subj_group.set("subj-group-type", "heading")
                        subject = SubElement(subj_group, "subject")
                        subject.text = article_category

    def set_kwd_group_research_organism(self, parent, poa_article):
        # kwd-group kwd-group-type="research-organism"
        self.kwd_group = SubElement(parent, "kwd-group")
        self.kwd_group.set("kwd-group-type", "research-organism")
        title = SubElement(self.kwd_group, "title")
        title.text = "Research organism"
        for research_organism in poa_article.research_organisms:
            kwd = SubElement(self.kwd_group, "kwd")
            kwd.text = research_organism

    def set_kwd_group_author_keywords(self, parent, poa_article):
        # kwd-group kwd-group-type="author-keywords"
        self.kwd_group = SubElement(parent, "kwd-group")
        self.kwd_group.set("kwd-group-type", "author-keywords")
        title = SubElement(self.kwd_group, "title")
        title.text = "Author keywords"
        for author_keyword in poa_article.author_keywords:
            kwd = SubElement(self.kwd_group, "kwd")
            kwd.text = author_keyword

    def set_funding_group(self, parent, poa_article):
        # funding-group
        self.funding_group = SubElement(parent, "funding-group")
        for index, award in enumerate(poa_article.funding_awards):
            par_id = "par-" + str(index + 1)
            self.set_award_group(self.funding_group, award, par_id)
        if poa_article.funding_note:
            self.funding_statement = SubElement(self.funding_group, "funding-statement")
            self.funding_statement.text = poa_article.funding_note

    def set_award_group(self, parent, award, par_id):
        award_group = SubElement(parent, "award-group")
        award_group.set("id", par_id)
        if award.institution_name or award.institution_id:
            self.set_funding_source(award_group, award.institution_id, award.institution_name)
        for award_id in award.award_ids:
            self.award_id = SubElement(award_group, "award-id")
            self.award_id.text = award_id
        if len(award.principal_award_recipients) > 0:
            self.set_principal_award_recipients(award_group, award)


    def set_funding_source(self, parent, institution_id, institution_name):
        self.funding_source = SubElement(parent, "funding-source")
        self.institution_wrap = SubElement(self.funding_source, "institution-wrap")
        if institution_id:
            self.institution_id = SubElement(self.institution_wrap, "institution-id")
            self.institution_id.set("institution-id-type", "FundRef")
            self.institution_id.text = "http://dx.doi.org/10.13039/" + institution_id
        if institution_name:
            self.institution = SubElement(self.institution_wrap, "institution")
            self.institution.text = eautils.entity_to_unicode(institution_name)

    def set_principal_award_recipients(self, parent, award):
        self.principal_award_recipient = SubElement(parent, "principal-award-recipient")
        for contributor in award.principal_award_recipients:
            self.set_name(self.principal_award_recipient, contributor)

    def set_volume(self, parent, poa_article):
        if poa_article.volume:
            self.volume = SubElement(parent, "volume")
            self.volume.text = str(poa_article.volume)

    def set_pub_date(self, parent, poa_article, pub_type):
        # pub-date pub-type = pub_type
        date = poa_article.get_date(pub_type)
        if date:
            if pub_type == "pub":
                self.pub_date = SubElement(parent, "pub-date")
                self.pub_date.set("date-type", pub_type)
                self.pub_date.set("publication-format", "electronic")
                self.set_dmy(self.pub_date, date)

    def set_date(self, parent, poa_article, date_type):
        # date date-type = date_type
        date = poa_article.get_date(date_type)
        if date:
            self.date = SubElement(parent, "date")
            self.date.set("date-type", date_type)
            self.set_dmy(self.date, date)

    def set_dmy(self, parent, date):
        day = SubElement(parent, "day")
        day.text = str(date.date.tm_mday).zfill(2)
        month = SubElement(parent, "month")
        month.text = str(date.date.tm_mon).zfill(2)
        year = SubElement(parent, "year")
        year.text = str(date.date.tm_year)

    def set_author_notes(self, parent, poa_article):
        self.author_notes = SubElement(parent, "author-notes")
        corresp_count = 0
        for contributor in poa_article.contributors:
            if contributor.corresp is True:
                corresp_count += 1
                self.set_corresp(self.author_notes, contributor, corresp_count)

    def set_corresp(self, parent, contributor, corresp_count):
        # For setting corresponding author tags in author-notes section

        # Look for the first email address in the contributors affiliations for now
        email = None
        for affiliation in contributor.affiliations:
            if affiliation.email:
                email = affiliation.email
                break
        initials = "" + contributor.given_name[0] + contributor.surname[0]
        if email:
            self.corresp = SubElement(parent, "corresp")
            self.corresp.set("id", "cor" + str(corresp_count))
            self.label = SubElement(self.corresp, "label")
            self.label.text = "*"
            self.label.tail = "For correspondence: "
            self.email = SubElement(self.corresp, "email")
            self.email.text = email
            self.email.tail = " (" + initials + ");"

    def set_history(self, parent, poa_article):
        self.history = SubElement(parent, "history")

        for date_type in self.jats_config.get('history_date_types'):
            date = poa_article.get_date(date_type)
            if date:
                self.set_date(self.history, poa_article, date_type)

    def output_xml(self, pretty=False, indent=""):
        publicId = '-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange DTD v1.1d3 20150301//EN'
        systemId = 'JATS-archivearticle1.dtd'
        encoding = 'utf-8'
        namespaceURI = None
        qualifiedName = "article"

        doctype = xmlio.ElifeDocumentType(qualifiedName)
        doctype._identified_mixin_init(publicId, systemId)

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)
        if doctype:
            reparsed.insertBefore(doctype, reparsed.documentElement)

        if pretty is True:
            return reparsed.toprettyxml(indent, encoding=encoding)
        else:
            return reparsed.toxml(encoding=encoding)


def write_xml_to_disk(article_xml, filename, output_dir=None):
    filename_path = filename
    if output_dir:
        filename_path = output_dir + os.sep + filename
    with open(filename_path, "wb") as fp:
        fp.write(article_xml.output_xml())

def build_article_from_csv(article_id, config_section="elife"):
    "build article objects populated with csv data"
    article, error_count, error_messages = parse.build_article(article_id)
    if article:
        return article
    else:
        logger.warning("the following article did not have enough components and " +
                       "xml was not generated " + str(article_id))
        logger.warning("warning count was " + str(error_count))
        if len(error_messages) > 0:
            logger.warning(", ".join(error_messages))
        return False

def build_xml(article_id, article=None, config_section="elife", add_comment=True):
    "generate xml from an article object"
    raw_config = config[config_section]
    jats_config = parse_raw_config(raw_config)
    if not article:
        article = build_article_from_csv(article_id, config_section)
    try:
        article_xml = ArticleXML(article, jats_config, add_comment)
        logger.info("generated xml for " + str(article_id))
        return article_xml
    except:
        return None

def build_xml_to_disk(article_id, article=None, config_section="elife", add_comment=True):
    "generate xml from an article object and write to disk"
    if not article:
        article = build_article_from_csv(article_id, config_section)
    article_xml = build_xml(article_id, article, config_section, add_comment)
    raw_config = config[config_section]
    jats_config = parse_raw_config(raw_config)
    if article_xml:
        filename = jats_config.get("xml_filename_pattern").format(
            manuscript=article.manuscript)
        try:
            write_xml_to_disk(article_xml, filename, output_dir=settings.TARGET_OUTPUT_DIR)
            logger.info("xml written for " + str(article_id))
            print("written " + str(article_id))
            return True
        except:
            logger.error("could not write xml for " + str(article_id))
            return False
    return False