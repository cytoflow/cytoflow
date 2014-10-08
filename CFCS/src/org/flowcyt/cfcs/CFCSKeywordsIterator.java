package org.flowcyt.cfcs;


import java.util.Iterator;

public class CFCSKeywordsIterator implements Iterator<String>
 {
    public CFCSKeywordsIterator(final CFCSKeywords keywords)
    {
        cfcsKeywords = keywords;
    }

    final CFCSKeywords cfcsKeywords;
    int index = 0;
    public final boolean hasNext()
    {
        return index < cfcsKeywords.getCount();
    }

    public final String next()
    {
        final CFCSKeyword keyword = cfcsKeywords.getKeyword(index);
        index++;
        return keyword.getKeywordName();
    }

    public final void remove()
    {
        final CFCSKeyword keyword = cfcsKeywords.getKeyword(index - 1);
        cfcsKeywords.deleteKeyword(keyword.getKeywordName());
    }
}
