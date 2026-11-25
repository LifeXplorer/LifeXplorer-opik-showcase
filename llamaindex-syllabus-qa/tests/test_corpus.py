from pypdf import PdfReader

from syllabus_qa import corpus


def test_every_policy_names_its_course_code():
    for syllabus in corpus.SYLLABI:
        for heading, body in syllabus.sections:
            assert syllabus.code in body, f"{syllabus.code} / {heading} lost its course code"


def test_render_writes_a_readable_pdf(tmp_path):
    path = corpus.render(corpus.SYLLABI[0], tmp_path)
    text = PdfReader(str(path)).pages[0].extract_text()
    assert "BIO 214" in text and "48 hours" in text


def test_ensure_corpus_only_generates_missing_files(tmp_path):
    first = corpus.ensure_corpus(tmp_path)
    stamp = first[0].stat().st_mtime_ns
    corpus.ensure_corpus(tmp_path)
    assert len(first) == 3 and first[0].stat().st_mtime_ns == stamp


def test_committed_pdfs_say_what_the_generator_says(tmp_path):
    for syllabus in corpus.SYLLABI:
        committed = PdfReader(str(corpus.SYLLABI_DIR / syllabus.filename)).pages[0].extract_text()
        fresh = PdfReader(str(corpus.render(syllabus, tmp_path))).pages[0].extract_text()
        assert committed == fresh
