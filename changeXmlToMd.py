import xml.etree.ElementTree as ET

def convert_to_markdown(xml_content):
    root = ET.fromstring(xml_content)
    markdown_content = []
    processed_tables = set()  # Track processed table IDs

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
        markdown_content.append(process_sections(sections, processed_tables))

    # Extract remaining tables not processed within sections
    tables = root.findall('.//table-wrap')
    if tables:
        unprocessed_tables = [table_wrap for table_wrap in tables if table_wrap.get('id') not in processed_tables]
        if unprocessed_tables:
            markdown_content.append("## Tables\n")
            for table_wrap in unprocessed_tables:
                label = table_wrap.find('label')
                caption = table_wrap.find('caption/p')
                table = table_wrap.find('table')
                if table is not None:
                    if label is not None:
                        markdown_content.append(f"**{extract_text(label)}**\n")
                    if caption is not None:
                        markdown_content.append(f"*{extract_text(caption)}*\n")
                    table_markdown = process_table(table)
                    markdown_content.append(table_markdown)
            markdown_content.append("")

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

    # Extract copyright information
    copyright_info = root.find('.//permissions/copyright-statement')
    if copyright_info is not None:
        markdown_content.append(f"**Copyright:** {extract_text(copyright_info)}\n")

    # Extract references
    references = root.findall('.//ref-list/ref')
    if references:
        markdown_content.append("## References\n")
        for ref in references:
            label = extract_text(ref.find('label'))
            citation = ref.find('.//element-citation')
            if citation is not None:
                authors = citation.findall('.//person-group[@person-group-type="author"]/name')
                author_list = ', '.join([f"{extract_text(a.find('surname'))} {extract_text(a.find('given-names'))}" for a in authors])
                article_title = extract_text(citation.find('article-title'))
                source = extract_text(citation.find('source'))
                year = extract_text(citation.find('year'))
                volume = extract_text(citation.find('volume'))
                fpage = extract_text(citation.find('fpage'))
                lpage = extract_text(citation.find('lpage'))
                doi = extract_text(citation.find('pub-id[@pub-id-type="doi"]'))
                
                ref_text = f"{label} {author_list}. {article_title}. *{source}*. {year};{volume}:{fpage}-{lpage}. DOI: {doi}"
                markdown_content.append(ref_text)
            else:
                # Handle mixed-citation
                mixed_citation = ref.find('mixed-citation')
                if mixed_citation is not None:
                    markdown_content.append(f"{label} {extract_text(mixed_citation)}")
        markdown_content.append("")

    return "\n".join(markdown_content)

def process_sections(sections, processed_tables):
    """Process section elements recursively to return their markdown representation."""
    content = []
    for sec in sections:
        title = sec.find('title')
        if title is not None:
            content.append(f"## {extract_text(title)}\n")
        for p in sec.findall('p'):
            content.append(f"{extract_text(p)}\n")
        # Process tables within sections
        tables = sec.findall('.//table-wrap')
        for table_wrap in tables:
            table_id = table_wrap.get('id')
            if table_id and table_id not in processed_tables:
                label = table_wrap.find('label')
                caption = table_wrap.find('caption/p')
                table = table_wrap.find('table')
                if table is not None:
                    if label is not None:
                        content.append(f"**{extract_text(label)}**\n")
                    if caption is not None:
                        content.append(f"*{extract_text(caption)}*\n")
                    table_markdown = process_table(table)
                    content.append(table_markdown)
                    processed_tables.add(table_id)
        # Recursively process subsections
        subsections = sec.findall('sec')
        if subsections:
            content.append(process_sections(subsections, processed_tables))
    return "\n".join(content)

def process_table(table_element):
    # Process the headers
    header_rows = []
    for header in table_element.findall('.//thead//tr'):
        row = []
        for cell in header.findall('th'):
            text = extract_text(cell)
            colspan = int(cell.attrib.get('colspan', '1'))
            rowspan = int(cell.attrib.get('rowspan', '1'))
            row.append((text, colspan, rowspan))
        header_rows.append(row)

    max_columns = max(len(row) for row in header_rows)  # Determine the maximum number of columns

    # Align headers with proper column span
    aligned_headers = align_headers(header_rows, max_columns)

    # Create Markdown headers
    markdown_header_rows = []
    for row in aligned_headers:
        # Ensure 'None' values are handled
        markdown_row = '| ' + ' | '.join([h[0] if h else '' for h in row]) + ' |'
        markdown_header_rows.append(markdown_row)

    header_row = '\n'.join(markdown_header_rows)
    
    # Construct the markdown table
    markdown_content = [header_row]

    # Add separator for markdown (align center by default)
    separator_row = '| ' + ' | '.join([':---:' for _ in range(max_columns)]) + ' |'
    markdown_content.append(separator_row)

    # Process the body rows
    for body_row in table_element.findall('.//tbody//tr'):
        cells = []
        for cell in body_row.findall('td'):
            text = extract_text(cell)
            cells.append(text)
        markdown_content.append('| ' + ' | '.join(cells) + ' |')

    return '\n'.join(markdown_content)


def align_headers(header_rows, max_columns):
    """Align headers considering colspan and rowspan."""
    aligned_headers = []
    temp_row = [None] * max_columns

    for row in header_rows:
        col_idx = 0
        temp_row = [None] * max_columns
        while col_idx < max_columns:
            if temp_row[col_idx] is not None:
                col_idx += 1
                continue

            if not row:
                break

            cell = row.pop(0)
            if len(cell) != 3:
                raise ValueError(f"Expected tuple of length 3, but got {len(cell)} elements: {cell}")

            text, colspan, rowspan = cell

            # Fill the colspan into the temp_row
            for i in range(colspan):
                if col_idx + i < max_columns:
                    temp_row[col_idx + i] = (text, rowspan)

            col_idx += colspan

        aligned_headers.append(temp_row)

    return aligned_headers


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
