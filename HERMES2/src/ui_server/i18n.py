#!/usr/bin/env python

########################################################
# i18n is the internationalization functions for
# the HERMES UI
########################################################
_hermes_svn_id_="$Id: i18n.py 1346 2013-07-02 20:32:25Z welling $"

# -*- coding: utf-8 -*-
 
import sys,os,os.path
import locale
import gettext
#import site_info



class i18n:
    localeDirIdentityFileName = 'hermes_locale_dir'

    def __init__(self, localeDir_ = "locale"):
        localeDir = None

        triedThese = []
        for parent in [os.getcwd()] + sys.path:
            candidatePath = os.path.join(parent,localeDir_)
            checkFile = os.path.join(candidatePath, i18n.localeDirIdentityFileName)
            if candidatePath.find('dist-packages') >= 0:
                continue
            elif os.path.exists(checkFile):
                localeDir = candidatePath
                break
            else:
                triedThese.append(candidatePath)

        if localeDir is None:
            print 'WARNING: Cannot find locale directory; tried %s'%triedThese
            print 'Internationalization will not be used'

        self.implemented = True
        self.localeDir = localeDir
        if localeDir is None:
            self.implemented = False
    
        if self.implemented:
            self.defaultLocale,self.defaultEncoding = locale.getdefaultlocale()

            ## Supported Languages
            print 'locale = <%s>, localeDir = <%s>'%(localeDir_, self.localeDir)
            langDirList = [s for s in os.listdir(self.localeDir) if s[0] != '.' and s != 'hermes_locale_dir']
            try:
                import zest.pocompile.compile
                for lang in langDirList:
                    zest.pocompile.compile.compile_po(self.localeDir+"/"+lang+"/LC_MESSAGES")
            except Exception as e:
                print "POCOMPILE didn't work"
                print str(e)
            self.supportedLocales = [lang for lang in langDirList \
                                     if "HERMES_UI.mo" in os.listdir(self.localeDir + "/" + lang + "/LC_MESSAGES")]
            if len(self.supportedLocales) == 0:
                self.implemented = False
            else:
                self.selectLocale(locale_=self.defaultLocale)

        else:
            self.defaultLocal = None
            self.defaultEncoding = None
            self.supportedLocales = []

    def __str__(self):
        if self.implemented:
            return "Internationalizer information: localeDir = %s,"\
                "defaultLocale = %s, defaultEncoding = %s, currentLocale = %s"\
                "supportedLocale = %s\n"%(self.localeDir,self.defaultLocale,
                                          self.defaultEncoding,
                                          self.currentLocaleName,
                                          str(self.supportedLocales))
        else:
            return "Internationalization not implmeneted"

    def __repr__(self):
        if self.implemented:
            return "Internationalizer information: \nlocaleDir = %s,"\
                "\ndefaultLocale = %s, \ndefaultEncoding = %s, "\
                "\ncurrentLocale = %s, "\
                "\nsupportedLocale = %s\n"%(self.localeDir,
                                            self.defaultLocale,
                                            self.defaultEncoding,
                                            self.currentLocaleName,
                                            str(self.supportedLocales))
        else:
            return "Internationalizaton not implmented"

    def selectLocale(self,locale_ = 'en_US',fallback_=False):
        if not self.implemented:
            self.currentLocaleName = locale_ # to avoid problems with help text generation
            return

        if locale_ not in self.supportedLocales:
            raise RuntimeError('Locale %s not supported in this install'%(locale_))
  
        templateDir = os.path.join(self.localeDir,locale_,'TEMPLATES')

        gettext.install(True, localedir=None,unicode=1)
        gettext.find('HERMES_UI',self.localeDir)
        gettext.textdomain('HERMES_UI')
        gettext.bind_textdomain_codeset('HERMES_UI','UTF-8')

        lang = gettext.translation('HERMES_UI',self.localeDir,languages=[locale_],fallback=fallback_)
        
        self.currentLocaleName = locale_
        self.currentLocale = lang
        self.currentTemplateDir = templateDir
        return

    def translateString(self,text):
        if not self.implemented:
            return text
        else:
            return self.currentLocale.ugettext(text)

    
def main():
    internationalizer = i18n()
    _=internationalizer.translateString
    
    print repr(internationalizer)
    print _("Tree Page")

    internationalizer.selectLocale("fr_FR")
    print str(internationalizer)
    print internationalizer.translateString("Tree Page")

### Main hook for unit testing
if __name__=="__main__":
    main()   
