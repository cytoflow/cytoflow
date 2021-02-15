

%define MODULEIMPORT
"
try:
  import _Logicle
except:
  from . import _Logicle
"
%enddef

%module Logicle

%{
#define SWIG_FILE_WITH_INIT
#include "logicle.h"
%}

%exception intScale {
   try {
      $action
   } catch (Logicle::IllegalArgument &e) {
      PyErr_SetString(PyExc_ValueError, const_cast<char*>(e.message()));
      return NULL;
   }
}

%exception inverse {
   try {
      $action
   } catch (Logicle::IllegalArgument &e) {
      PyErr_SetString(PyExc_ValueError, const_cast<char*>(e.message()));
      return NULL;
   }
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

