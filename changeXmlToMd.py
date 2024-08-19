import xml.etree.ElementTree as ET

def remove_unwanted_tags(root, tags_to_remove):
    # Find all specified tags and remove them from their parent
    for tag in tags_to_remove:
        for element in root.findall(f'.//{tag}'):
            parent = root.find(f".//{element.tag}/..")  # Find the parent of the element
            if parent is not None:
                parent.remove(element)

def convert_to_markdown(xml_content):
    root = ET.fromstring(xml_content)

    # Remove all <table-wrap> and <fig> elements
    remove_unwanted_tags(root, tags_to_remove=['table-wrap', 'fig'])

    markdown_content = []

    # Extract article title
    title = root.find('.//title-group/article-title')
    if title is not None:
        markdown_content.append(f"# {extract_text(title)}\n")

    # Extract authors
    authors = root.findall('.//contrib-group/contrib/name')
    if authors:
        author_names = [f"{extract_text(author.find('given-names'))} {extract_text(author.find('surname'))}" for author in authors]
        markdown_content.append(f"**Authors:** {', '.join(author_names)}\n")

    # Extract article IDs
    article_ids = root.findall('.//article-id')
    if article_ids:
        markdown_content.append("**Article IDs:**")
        for article_id in article_ids:
            markdown_content.append(f"- {article_id.attrib['pub-id-type'].capitalize()}: {extract_text(article_id)}")
        markdown_content.append("")

    # Extract categories
    categories = root.findall('.//article-categories/subj-group/subject')
    if categories:
        markdown_content.append("**Categories:**")
        for category in categories:
            markdown_content.append(f"- {extract_text(category)}")
        markdown_content.append("")

    # Extract publication dates
    pub_dates = root.findall('.//pub-date')
    if pub_dates:
        markdown_content.append("**Publication Dates:**")
        for pub_date in pub_dates:
            date_type = pub_date.attrib.get('pub-type', 'Publication')
            date_string = '-'.join([extract_text(pub_date.find(tag)) for tag in ('day', 'month', 'year') if pub_date.find(tag) is not None])
            markdown_content.append(f"- {date_type.capitalize()}: {date_string}")
        markdown_content.append("")

    # Extract abstract
    abstract = root.find('.//abstract')
    if abstract is not None:
        markdown_content.append("## Abstract\n")
        for sec in abstract.findall('.//sec'):
            section_title = sec.find('title')
            if section_title is not None:
                markdown_content.append(f"### {extract_text(section_title)}\n")
            for p in sec.findall('p'):
                markdown_content.append(f"{extract_text(p)}\n")

    # Extract sections from body
    body = root.find('.//body')
    if body is not None:
        sections = body.findall('sec')
        markdown_content.append(process_sections(sections))

    # Extract keywords
    keywords = root.findall('.//kwd-group/kwd')
    if keywords:
        markdown_content.append("**Keywords:**")
        markdown_content.append(', '.join(extract_text(kwd) for kwd in keywords))
        markdown_content.append("")

    # Extract funding information
    funding_sources = root.findall('.//funding-group/award-group')
    if funding_sources:
        markdown_content.append("**Funding Sources:**")
        for award in funding_sources:
            institution = award.find('.//funding-source/institution-wrap/institution')
            if institution is not None:
                markdown_content.append(f"- Institution: {extract_text(institution)}")
            institution_id = award.find('.//funding-source/institution-wrap/institution-id')
            if institution_id is not None:
                markdown_content.append(f"  - Institution ID: {extract_text(institution_id)}")
            award_id = award.find('.//award-id')
            if award_id is not None:
                markdown_content.append(f"  - Award ID: {extract_text(award_id)}")
            principal_investigator = award.find('.//principal-award-recipient/name')
            if principal_investigator is not None:
                pi_name = f"{extract_text(principal_investigator.find('given-names'))} {extract_text(principal_investigator.find('surname'))}"
                markdown_content.append(f"  - Principal Investigator: {pi_name}")
        markdown_content.append("")

    # Extract references
    references = root.findall('.//ref-list/ref')
    if references:
        markdown_content.append("## References\n")
        for ref in references:
            label = extract_text(ref.find('label'))
            citation = ref.find('.//mixed-citation') or ref.find('.//element-citation')
            if citation is not None:
                citation_text = extract_citation(citation)
                markdown_content.append(f"{label}. {citation_text}")
        markdown_content.append("")

    return "\n".join(markdown_content)

def process_sections(sections):
    """Process section elements recursively to return their markdown representation, ignoring tables and figures."""
    content = []
    for sec in sections:
        title = sec.find('title')
        if title is not None:
            content.append(f"## {extract_text(title)}\n")
        for p in sec.findall('p'):
            content.append(f"{extract_text(p)}\n")
        # Recursively process subsections
        subsections = sec.findall('sec')
        if subsections:
            content.append(process_sections(subsections))
    return "\n".join(content)

def extract_citation(citation_element):
    """Extract and format the citation text from a mixed-citation or element-citation element."""
    person_group = citation_element.find('.//person-group')
    authors = []
    if person_group is not None:
        for name in person_group.findall('name'):
            surname = extract_text(name.find('surname'))
            given_names = extract_text(name.find('given-names'))
            authors.append(f"{surname} {given_names}")
        if citation_element.find('etal') is not None:
            authors.append('et al.')

    article_title = extract_text(citation_element.find('article-title'))
    source = extract_text(citation_element.find('source'))
    year = extract_text(citation_element.find('year'))
    volume = extract_text(citation_element.find('volume'))
    fpage = extract_text(citation_element.find('fpage'))
    lpage = extract_text(citation_element.find('lpage'))
    doi = extract_text(citation_element.find('.//pub-id[@pub-id-type="doi"]'))
    pmid = extract_text(citation_element.find('.//pub-id[@pub-id-type="pmid"]'))

    citation_text = f"{', '.join(authors)}. {article_title}. *{source}*. {year};{volume}:{fpage}-{lpage}."
    if doi:
        citation_text += f" DOI: {doi}."
    if pmid:
        citation_text += f" PMID: {pmid}."

    return citation_text

def extract_text(element):
    """Extract text content from an XML element, handling None gracefully."""
    if element is None:
        return ""
    return ''.join(element.itertext()).strip() if element.text is not None else ""

def read_xml_file(file_path):
    """Reads the content of an XML file and returns it as a string."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_markdown_file(markdown_text, filename="outputMds/PMC11207375.md"):
    """Save the generated markdown text to a file."""
    with open(filename, "w") as file:
        file.write(markdown_text)

if __name__ == "__main__":
    # Read the XML content from a file
    xml_content = read_xml_file("testXmls/PMC11207375.xml")

    # Convert XML to Markdown
    markdown_text = convert_to_markdown(xml_content)
    
    # Save Markdown to a file
    save_markdown_file(markdown_text)
