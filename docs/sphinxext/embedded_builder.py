from sphinx.builders.html import StandaloneHTMLBuilder

class EmbeddedHTMLBuilder(StandaloneHTMLBuilder):
    name = 'user_manual'
    
def setup(app):
    app.add_builder(EmbeddedHTMLBuilder)