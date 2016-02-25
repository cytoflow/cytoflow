#ifdef R_LOGICLE
#include <R.h>
#include <Rinternals.h>
#include <R_ext/Rdynload.h>
#endif

#ifdef __cplusplus
#include <vector>

extern "C" {

#endif

        struct logicle_params
        {
                double T, W, M, A;

                double a, b, c, d, f;
                double w, x0, x1, x2;

                double xTaylor;
                double *taylor;

                double *lookup;
                int bins;
        };

        const char * logicle_error ();
        const struct logicle_params * logicle_create (double T, double W, double M, double A, int bins);
        void logicle_destroy (const struct logicle_params * params);
        double logicle_scale (const struct logicle_params * logicle, double value);
        int logicle_int_scale (const struct logicle_params * logicle, double value);
        double logicle_inverse (const struct logicle_params * logicle, double scale);
        double logicle_int_inverse (const struct logicle_params * logicle, int scale);
        double logicle_T (const struct logicle_params * logicle);
        double logicle_W (const struct logicle_params * logicle);
        double logicle_M (const struct logicle_params * logicle);
        double logicle_A (const struct logicle_params * logicle);
        double logicle_bins (const struct logicle_params * logicle);
#ifdef R_LOGICLE
        SEXP R_create(SEXP T, SEXP M, SEXP W, SEXP A, SEXP bins);
        void R_destroy(SEXP logicle);
        void R_scale(SEXP p, int* n, double* x, double* y);
        void R_intScale(SEXP p, int* n, double* x, int* y);
        void R_inverse(SEXP p, int* n, double* x, double* y);
        void R_intInverse(SEXP p, int* n, int* x, double* y);
        SEXP R_T (SEXP pp);
        SEXP R_W (SEXP pp);
        SEXP R_M (SEXP pp);
        SEXP R_A (SEXP pp);
        SEXP R_bins (SEXP pp);
#endif

#ifdef __cplusplus

}

class Logicle
{
public:
        static const double DEFAULT_DECADES;

        class Exception
        {
        public:
                Exception (const Exception & e);

                virtual ~Exception ();

                const char * message () const;

        protected:
                char * buffer;

                Exception ();
                Exception (const char * const message);

        private:
                Exception & operator= (const Exception & e);

                friend class Logicle;
        };

        class IllegalArgument : public Exception
        {
        private:
                IllegalArgument (double value);
                IllegalArgument (int value);

                friend class Logicle;
                friend class FastLogicle;
        };

        class IllegalParameter : public Exception
        {
        private:
                IllegalParameter (const char * const message);

                friend class Logicle;
        };

        class DidNotConverge : public Exception
        {
        private:
                DidNotConverge (const char * const message);

                friend class Logicle;
        };

        Logicle (double T, double W, double M = DEFAULT_DECADES, double A = 0);
        Logicle (const Logicle & logicle);

        virtual ~Logicle ();

        inline double T() const { return p->T; };
        inline double W() const { return p->W; };
        inline double M() const { return p->M; };
        inline double A() const { return p->A; };

        inline double a() const { return p->a; };
        inline double b() const { return p->b; };
        inline double c() const { return p->c; };
        inline double d() const { return p->d; };
        inline double f() const { return p->f; };

        inline double w() const { return p->w; };
        inline double x0() const { return p->x0; };
        inline double x1() const { return p->x1; };
        inline double x2() const { return p->x2; };

        virtual double scale (double value) const;
        virtual double inverse (double scale) const;
        double dynamicRange () const;
        void axisLabels (std::vector<double> & label) const;

protected:
        static const double LN_10;
        static const double EPSILON;
        static const double NaN;
        static const int TAYLOR_LENGTH;

        logicle_params * p;

        Logicle (double T, double W, double M, double A, int bins);

        static double solve (double b, double w);

        double slope (double scale) const;
        double seriesBiexponential (double scale) const;

private:
        Logicle & operator= (const Logicle & logicle);

        void initialize (double T, double W, double M, double A, int bins);

        friend class TestLogicle;
};

class FastLogicle : public Logicle
{
public:
        static const int DEFAULT_BINS;

        FastLogicle (double T, double W, double M, double A, int bins);
        FastLogicle (double T, double W, double M, int bins);
        FastLogicle (double T, double W, int bins);

        FastLogicle (double T, double W, double M, double A);
        FastLogicle (double T, double W, double M);
        FastLogicle (double T, double W);

        FastLogicle (const FastLogicle & logicle);

        virtual ~FastLogicle ();

        virtual double scale (double value) const;
        virtual double inverse (double scale) const;

        inline int bins () const { return p->bins; };

        int intScale (double value) const;
        double inverse (int scale) const;

private:
        void initialize (int bins);

        friend class TestLogicle;
};

// Visual C++ hack!
int PullInMyLibrary ();

#endif
