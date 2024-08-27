import time
from xml.etree.ElementTree import Element, SubElement
from elifearticle import utils as eautils
from elifetools import utils as etoolsutils
from jatsgenerator import utils


def set_journal_title_group(parent, journal_title):
    # journal-title-group
    journal_title_group = SubElement(parent, "journal-title-group")

    # journal-title
    journal_title_tag = SubElement(journal_title_group, "journal-title")
    journal_title_tag.text = journal_title


def set_fn_group_competing_interest(parent, poa_article):
    competing_interest = SubElement(parent, "fn-group")
    competing_interest.set("content-type", "competing-interest")
    title = SubElement(competing_interest, "title")
    title.text = "Competing interest"

    # Check if we are supplied a conflict default statement and set count accordingly
    if poa_article.conflict_default:
        conflict_count = 1
    else:
        conflict_count = 0

    for contributor in poa_article.contributors:
        if contributor.conflict:
            for conflict in contributor.conflict:
                conf_id = "conf" + str(conflict_count + 1)
                fn_tag = SubElement(competing_interest, "fn")
                fn_tag.set("fn-type", "conflict")
                fn_tag.set("id", conf_id)
                tag_name = "p"
                conflict_text = (
                    contributor.given_name
                    + " "
                    + contributor.surname
                    + ", "
                    + conflict
                    + "."
                )
                utils.append_to_tag(fn_tag, tag_name, conflict_text)
                # increment
                conflict_count = conflict_count + 1
    if poa_article.conflict_default:
        # default for contributors with no conflicts
        if conflict_count > 1:
            # Change the default conflict text
            conflict_text = (
                "The other authors declare that no competing interests exist."
            )
        else:
            conflict_text = poa_article.conflict_default
        conf_id = "conf1"
        fn_tag = SubElement(competing_interest, "fn")
        fn_tag.set("fn-type", "conflict")
        fn_tag.set("id", conf_id)
        p_tag = SubElement(fn_tag, "p")
        p_tag.text = conflict_text
        conflict_count = conflict_count + 1


def set_fn_group_ethics_information(parent, poa_article):
    ethics_fn_group = SubElement(parent, "fn-group")
    ethics_fn_group.set("content-type", "ethics-information")
    title = SubElement(ethics_fn_group, "title")
    title.text = "Ethics"

    for ethic in poa_article.ethics:
        fn_tag = SubElement(ethics_fn_group, "fn")
        fn_tag.set("fn-type", "other")
        p_tag = SubElement(fn_tag, "p")
        p_tag.text = ethic


def set_name(parent, contributor):
    name = SubElement(parent, "name")
    surname = SubElement(name, "surname")
    surname.text = contributor.surname
    given_name = SubElement(name, "given-names")
    given_name.text = contributor.given_name
    if contributor.suffix:
        suffix = SubElement(name, "suffix")
        suffix.text = contributor.suffix


def set_anonymous(parent):
    SubElement(parent, "anonymous")


def set_contrib_name(parent, contributor):
    if contributor.collab:
        collab_tag = SubElement(parent, "collab")
        collab_tag.text = contributor.collab
    elif hasattr(contributor, "anonymous") and contributor.anonymous:
        set_anonymous(parent)
    else:
        set_name(parent, contributor)


def set_contrib_role(parent, contrib_type, contributor=None):
    if contributor and hasattr(contributor, "roles") and contributor.roles:
        for role in contributor.roles:
            role_tag = SubElement(parent, "role")
            if role.specific_use:
                role_tag.set("specific-use", role.specific_use)
            if role.text:
                role_tag.text = role.text
    elif contrib_type == "editor":
        role_tag = SubElement(parent, "role")
        role_tag.text = "Reviewing editor"


def set_contrib_orcid(parent, contributor):
    if contributor.orcid:
        orcid_value = etoolsutils.orcid_uri_to_orcid(contributor.orcid)
        orcid_tag = SubElement(parent, "contrib-id")
        if contributor.orcid_authenticated:
            orcid_tag.set("authenticated", "true")
        orcid_tag.set("contrib-id-type", "orcid")
        orcid_tag.text = "http://orcid.org/" + orcid_value


def set_contrib_corresp(parent, rid):
    # Corresponding author xref tag logic
    xref_tag = SubElement(parent, "xref")
    xref_tag.set("ref-type", "corresp")
    xref_tag.set("rid", rid)
    xref_tag.text = "*"


def set_contrib_funding(parent, poa_article, contributor):
    for par_id in get_contrib_par_ids(poa_article, contributor.auth_id):
        xref_tag = SubElement(parent, "xref")
        xref_tag.set("ref-type", "other")
        xref_tag.set("rid", par_id)


def set_contrib_conflict(parent, contrib_type, rid):
    # Contrib conflict xref
    if rid and contrib_type and contrib_type != "editor":
        xref_tag = SubElement(parent, "xref")
        xref_tag.set("ref-type", "fn")
        xref_tag.set("rid", rid)


def set_aff(
    parent, affiliation, contrib_type, aff_id=None, tail=", ", institution_wrap=None
):
    aff = SubElement(parent, "aff")

    if aff_id:
        aff.set("id", aff_id)

    # if there is text and no other essential attributes, set the text and return
    essential_attributes = ["institution"]
    if (
        affiliation.text
        and len([name for name in essential_attributes if getattr(affiliation, name)])
        <= 0
    ):
        aff.text = affiliation.text
        return

    if institution_wrap:
        institution_parent_tag = SubElement(aff, "institution-wrap")
    else:
        institution_parent_tag = aff

    if affiliation.ror:
        institution_id = SubElement(institution_parent_tag, "institution-id")
        institution_id.set("institution-id", "ror")
        institution_id.text = affiliation.ror

    if contrib_type != "editor":
        if affiliation.department:
            department = SubElement(institution_parent_tag, "institution")
            department.set("content-type", "dept")
            department.text = affiliation.department
            if tail:
                department.tail = tail

    if affiliation.institution:
        institution = SubElement(institution_parent_tag, "institution")
        institution.text = affiliation.institution
        if tail:
            institution.tail = tail

    if affiliation.city:
        addline = SubElement(aff, "addr-line")
        city = SubElement(addline, "named-content")
        city.set("content-type", "city")
        city.text = affiliation.city
        if tail:
            addline.tail = tail

    if affiliation.country:
        country = SubElement(aff, "country")
        country.text = affiliation.country

    if affiliation.phone:
        phone = SubElement(aff, "phone")
        phone.text = affiliation.phone

    if affiliation.fax:
        fax = SubElement(aff, "fax")
        fax.text = affiliation.fax


def set_article_datasets_header(parent):
    sec_title = SubElement(parent, "title")
    sec_title.text = "Data availability"


def set_data_availability(parent, poa_article):
    if poa_article.data_availability:
        tag_name = "p"
        utils.append_to_tag(parent, tag_name, poa_article.data_availability)


def set_dataset(parent, dataset, dataro_num, specific_use=None):
    element_citation_tag = SubElement(parent, "element-citation")
    element_citation_tag.set("id", "dataset" + str(dataro_num))
    element_citation_tag.set("publication-type", "data")
    if specific_use:
        element_citation_tag.set("specific-use", specific_use)

    if dataset.authors:
        person_group_tag = SubElement(element_citation_tag, "person-group")
        person_group_tag.set("person-group-type", "author")
        for author in dataset.authors:
            collab = SubElement(person_group_tag, "collab")
            collab.text = author

    if dataset.year:
        year = SubElement(element_citation_tag, "year")
        year.text = dataset.year
        year.set("iso-8601-date", dataset.year)

    if dataset.title:
        source = SubElement(element_citation_tag, "source")
        source.text = dataset.title

    if dataset.source_id:
        ext_link_tag = SubElement(element_citation_tag, "ext-link")
        ext_link_tag.text = dataset.source_id
        ext_link_tag.set("ext-link-type", "uri")
        ext_link_tag.set("xlink:href", dataset.source_id)

    if dataset.license_info:
        comment = SubElement(element_citation_tag, "comment")
        comment.text = dataset.license_info


def set_title_group(parent, poa_article):
    """
    Allows the addition of XML tags
    """
    root_tag_name = "title-group"
    tag_name = "article-title"
    root_xml_element = Element(root_tag_name)
    new_tag = utils.append_to_tag(root_xml_element, tag_name, poa_article.title)
    parent.append(new_tag)


def set_history(parent, poa_article, date_types):
    history = SubElement(parent, "history")
    for date_type in date_types:
        date = poa_article.get_date(date_type)
        if date:
            set_date(history, poa_article, date_type)


def set_publication_history(parent, poa_article):
    pub_history = SubElement(parent, "pub-history")
    for event in poa_article.publication_history:
        event_tag = SubElement(pub_history, "event")
        if event.event_desc:
            event_desc_tag = SubElement(event_tag, "event-desc")
            event_desc_tag.text = event.event_desc
        if event.date:
            event_date_tag = SubElement(event_tag, "date")
            event_date_tag.set("date-type", event.event_type)
            event_date_tag.set("iso-8601-date", time.strftime("%Y-%m-%d", event.date))
            set_dmy(event_date_tag, event.date)
        if event.uri:
            self_uri_tag = SubElement(event_tag, "self-uri")
            self_uri_tag.set("content-type", event.event_type)
            self_uri_tag.set("xlink:href", event.uri)


def set_sub_articles(parent, article):
    for review_article in article.review_articles:
        set_sub_article(parent, review_article)


def set_sub_article(parent, article):
    sub_article_tag = SubElement(parent, "sub-article")
    if article.id:
        sub_article_tag.set("id", article.id)
    if article.article_type:
        sub_article_tag.set("article-type", article.article_type)
    front_stub_tag = SubElement(sub_article_tag, "front-stub")
    set_article_id(front_stub_tag, article)
    set_title_group(front_stub_tag, article)
    if article.contributors:
        for contributor in article.contributors:
            contrib_group_tag = SubElement(front_stub_tag, "contrib-group")
            contrib_tag = SubElement(contrib_group_tag, "contrib")
            contrib_tag.set("contrib-type", contributor.contrib_type)
            set_contrib_name(contrib_tag, contributor)
            set_contrib_orcid(contrib_tag, contributor)
            # add inline aff tags
            for affiliation in contributor.affiliations:
                set_aff(
                    contrib_tag,
                    affiliation,
                    contributor.contrib_type,
                    institution_wrap=True,
                )


def set_license(parent, poa_article):
    license_tag = SubElement(parent, "license")

    license_tag.set("xlink:href", poa_article.license.href)

    license_p = SubElement(license_tag, "license-p")
    license_p.text = poa_article.license.paragraph1

    ext_link = SubElement(license_p, "ext-link")
    ext_link.set("ext-link-type", "uri")
    ext_link.set("xlink:href", poa_article.license.href)
    ext_link.text = poa_article.license.name
    ext_link.tail = poa_article.license.paragraph2


def set_copyright(parent, poa_article):
    # Count authors (non-editors)
    non_editor = []
    for contributor in poa_article.contributors:
        if contributor.contrib_type != "editor" and contributor.surname:
            non_editor.append(contributor)

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

    copyright_statement = "\u00a9 " + str(copyright_year) + ", " + copyright_holder
    copyright_tag = SubElement(parent, "copyright-statement")
    copyright_tag.text = copyright_statement

    # copyright-year
    copyright_year_tag = SubElement(parent, "copyright-year")
    copyright_year_tag.text = str(copyright_year)

    # copyright-holder
    copyright_holder_tag = SubElement(parent, "copyright-holder")
    copyright_holder_tag.text = copyright_holder


def set_permissions(parent, poa_article):
    permissions = SubElement(parent, "permissions")
    if poa_article.license.copyright is True:
        set_copyright(permissions, poa_article)
    set_license(permissions, poa_article)


def set_abstract(parent, poa_article):
    """
    Allows the addition of XML tags
    """
    root_tag_name = "abstract"
    tag_name = "p"

    # do not double-wrap in a p tag
    if poa_article.abstract.startswith("<p>"):
        # note: multiple p tag content will be collapsed into one p tag for now
        abstract_text = etoolsutils.remove_tag("p", poa_article.abstract)
    else:
        abstract_text = poa_article.abstract

    root_xml_element = Element(root_tag_name)
    new_tag = utils.append_to_tag(
        root_xml_element, tag_name, abstract_text, utils.XML_NAMESPACE_MAP
    )

    parent.append(new_tag)


def get_contrib_par_ids(poa_article, auth_id):
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


def compare_aff(aff1, aff2):
    # Compare two affiliations by comparing the object attributes
    attrs = ["city", "country", "department", "institution"]
    # if all attributes are empty, check the text attribute
    if len([name for name in attrs if getattr(aff1, name)]) <= 0:
        attrs = ["text"]

    for attr in attrs:
        if (
            getattr(aff1, attr)
            and getattr(aff2, attr)
            and getattr(aff1, attr) != getattr(aff2, attr)
        ):
            return False
    return True


def do_display_channel(poa_article):
    "decide whether to add a display-channel"
    if (
        poa_article.get_display_channel()
        and poa_article.get_display_channel().strip() != ""
    ):
        return True
    return False


def do_article_categories(poa_article):
    "check whether we will add any article-categories values"
    return bool(do_display_channel(poa_article) or do_subject_heading(poa_article))


def do_subject_heading(poa_article):
    "decide whether to add subject headings from article_categories"
    if poa_article.article_categories:
        for heading in poa_article.article_categories:
            if heading and heading.strip() != "":
                return True
    return False


def set_article_categories(parent, poa_article):
    # article-categories
    if do_article_categories(poa_article):
        article_categories = SubElement(parent, "article-categories")

        if do_display_channel(poa_article):
            # subj-group subj-group-type="display-channel"
            subj_group = SubElement(article_categories, "subj-group")
            subj_group.set("subj-group-type", "display-channel")
            subject = SubElement(subj_group, "subject")
            subject.text = poa_article.get_display_channel()

        if do_subject_heading(poa_article):
            for article_category in poa_article.article_categories:
                # subj-group subj-group-type="heading"
                if article_category and article_category.rstrip().lstrip() != "":
                    subj_group = SubElement(article_categories, "subj-group")
                    subj_group.set("subj-group-type", "heading")
                    subject = SubElement(subj_group, "subject")
                    subject.text = article_category


def set_kwd_group_research_organism(parent, poa_article):
    # kwd-group kwd-group-type="research-organism"
    kwd_group = SubElement(parent, "kwd-group")
    kwd_group.set("kwd-group-type", "research-organism")
    title = SubElement(kwd_group, "title")
    title.text = "Research organism"
    for research_organism in poa_article.research_organisms:
        parent_tag = kwd_group
        tag_name = "kwd"
        utils.append_to_tag(parent_tag, tag_name, research_organism)


def set_kwd_group_author_keywords(parent, poa_article):
    # kwd-group kwd-group-type="author-keywords"
    kwd_group = SubElement(parent, "kwd-group")
    kwd_group.set("kwd-group-type", "author-keywords")
    title = SubElement(kwd_group, "title")
    title.text = "Author keywords"
    for author_keyword in poa_article.author_keywords:
        kwd = SubElement(kwd_group, "kwd")
        kwd.text = author_keyword


def set_funding_group(parent, poa_article):
    # funding-group
    funding_group = SubElement(parent, "funding-group")
    for index, award in enumerate(poa_article.funding_awards):
        par_id = "par-" + str(index + 1)
        set_award_group(funding_group, award, par_id)
    if poa_article.funding_note:
        funding_statement = SubElement(funding_group, "funding-statement")
        funding_statement.text = poa_article.funding_note


def set_award_group(parent, award, par_id):
    award_group = SubElement(parent, "award-group")
    award_group.set("id", par_id)
    if award.institution_name or award.institution_id:
        set_funding_source(award_group, award.institution_id, award.institution_name)
    for award_object in award.awards:
        if award_object.award_id:
            award_id_tag = SubElement(award_group, "award-id")
            award_id_tag.text = award_object.award_id
    if award.principal_award_recipients:
        set_principal_award_recipients(award_group, award)


def set_funding_source(parent, institution_id, institution_name):
    funding_source = SubElement(parent, "funding-source")
    institution_wrap = SubElement(funding_source, "institution-wrap")
    if institution_id:
        institution_id_tag = SubElement(institution_wrap, "institution-id")
        institution_id_tag.set("institution-id-type", "FundRef")
        institution_id_tag.text = "http://dx.doi.org/10.13039/" + institution_id
    if institution_name:
        institution_tag = SubElement(institution_wrap, "institution")
        institution_tag.text = eautils.entity_to_unicode(institution_name)


def set_principal_award_recipients(parent, award):
    principal_award_recipient_tag = SubElement(parent, "principal-award-recipient")
    for contributor in award.principal_award_recipients:
        set_name(principal_award_recipient_tag, contributor)


def set_volume(parent, poa_article):
    if poa_article.volume:
        volume = SubElement(parent, "volume")
        volume.text = str(poa_article.volume)


def set_pub_date(parent, poa_article, pub_type):
    # pub-date pub-type = pub_type
    date = poa_article.get_date(pub_type)
    if date:
        if pub_type in ["posted_date", "pub"]:
            date_tag = SubElement(parent, "pub-date")
            date_tag.set("date-type", pub_type)
            date_tag.set("publication-format", "electronic")
            set_dmy(date_tag, date.date)


def set_date(parent, poa_article, date_type):
    # date date-type = date_type
    date = poa_article.get_date(date_type)
    if date:
        date_tag = SubElement(parent, "date")
        date_tag.set("date-type", date_type)
        set_dmy(date_tag, date.date)


def set_dmy(parent, date):
    day = SubElement(parent, "day")
    day.text = str(date.tm_mday).zfill(2)
    month = SubElement(parent, "month")
    month.text = str(date.tm_mon).zfill(2)
    year = SubElement(parent, "year")
    year.text = str(date.tm_year)


def set_author_notes(parent, poa_article):
    author_notes = SubElement(parent, "author-notes")
    corresp_count = 0
    for contributor in poa_article.contributors:
        if contributor.corresp is True:
            corresp_count += 1
            set_corresp(author_notes, contributor, corresp_count)


def set_corresp(parent, contributor, corresp_count):
    # For setting corresponding author tags in author-notes section

    # Look for the first email address in the contributors affiliations for now
    email = None
    for affiliation in contributor.affiliations:
        if affiliation.email:
            email = affiliation.email
            break
    # concatenate initials for the contributor
    initials = "".join(
        [
            name_part[0]
            for name_part in [contributor.given_name, contributor.surname]
            if name_part
        ]
    )
    if email:
        corresp = SubElement(parent, "corresp")
        corresp.set("id", "cor" + str(corresp_count))
        label = SubElement(corresp, "label")
        label.text = "*"
        label.tail = "For correspondence: "
        email_tag = SubElement(corresp, "email")
        email_tag.text = email
        email_tag.tail = " (" + initials + ");"


def set_article_id(parent, article):
    if article.doi:
        doi_tag = SubElement(parent, "article-id")
        doi_tag.set("pub-id-type", "doi")
        doi_tag.text = article.doi


def set_related_object(parent, article):
    # add related-object link to Editor's evaluation
    related_object_num = 1
    for related_material in article.related_articles:
        if related_material.ext_link_type and related_material.xlink_href:
            related_object_tag = SubElement(parent, "related-object")
            related_object_tag.set("id", "%sro%s" % (article.id, related_object_num))
            related_object_tag.set("object-id-type", "id")
            related_object_tag.set(
                "object-id", utils.object_id_from_uri(related_material.xlink_href)
            )
            related_object_tag.set("link-type", related_material.ext_link_type)
            related_object_tag.set("xlink:href", related_material.xlink_href)
            related_object_num += 1


def set_body(parent, article):
    "set body tag"
    body_tag = SubElement(parent, "body")
    if hasattr(article, "content_blocks") and article.content_blocks:
        set_content_blocks(body_tag, article.content_blocks)
    return body_tag


# max level of recursion adding content blocks supported
MAX_LEVEL = 5


def set_content_blocks(parent, content_blocks, level=1):
    "used when setting body content"
    if level > MAX_LEVEL:
        raise Exception("Maximum level of nested content blocks reached")
    for block in content_blocks:
        block_tag = None
        if block.block_type in [
            "boxed-text",
            "disp-formula",
            "disp-quote",
            "fig",
            "list",
            "media",
            "p",
            "table-wrap",
        ]:
            # retain standard tag attributes as well as any specific ones from the block object
            if block.content:
                utils.append_to_tag(
                    parent,
                    block.block_type,
                    block.content,
                    utils.XML_NAMESPACE_MAP,
                    attributes=block.attr_names(),
                    attributes_text=block.attr_string(),
                )
                block_tag = parent[-1]
            else:
                # add empty tags too
                block_tag = SubElement(parent, block.block_type)
                block_tag.text = block.content
                for key, value in block.attr.items():
                    block_tag.set(key, value)
        if block_tag is not None and block.content_blocks:
            # recursion
            set_content_blocks(block_tag, block.content_blocks, level + 1)
