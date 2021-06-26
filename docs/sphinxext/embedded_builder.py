from sphinx.builders.html import StandaloneHTMLBuilder

class EmbeddedHTMLBuilder(StandaloneHTMLBuilder):
    name = 'embedded_help'
    
def setup(app):
    app.add_builder(EmbeddedHTMLBuilder)