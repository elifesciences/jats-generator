elifeLibrary {
    stage 'Checkout', {
        checkout scm
    }

    stage 'Project tests', {
        try {
            elifeLocalTests "./project_tests.sh"
        } finally {
            archive 'xml_gen.log'
            archive 'parse.log'
        }
    }
}
