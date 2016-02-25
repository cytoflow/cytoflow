#include "logicle.h"
#include <memory.h>
#include <cstring>
#include <cstdio>
#include <cmath>
#include <limits>

const double Logicle::DEFAULT_DECADES = 4.5;

const double Logicle::LN_10 = log(10.);
const double Logicle::EPSILON = std::numeric_limits<double>::epsilon();
const double Logicle::NaN = std::numeric_limits<double>::quiet_NaN();

const int Logicle::TAYLOR_LENGTH = 16;

Logicle::Exception::Exception()
{
	buffer = 0;
}

Logicle::Exception::Exception(const Logicle::Exception & e)
{
	buffer = strdup(e.buffer);
}

Logicle::Exception::Exception (const char * const message)
{
	buffer = strdup(message);
}

Logicle::Exception::~Exception ()
{
	delete buffer;
}

const char * Logicle::Exception::message () const
{
	return buffer;
}

Logicle::IllegalArgument::IllegalArgument (double value)
{
	buffer = new char[128];
	sprintf(buffer, "Illegal argument value %.17g", value);
}

Logicle::IllegalArgument::IllegalArgument (int value)
{
	buffer = new char[128];
	sprintf(buffer, "Illegal argument value %d", value);
}

Logicle::IllegalParameter::IllegalParameter (const char * const message) : Exception(message)
{	}

Logicle::DidNotConverge::DidNotConverge(const char * const message) : Exception(message)
{	}

void Logicle::initialize (double T, double W, double M, double A, int bins)
{
	// allocate the parameter structure
	p = new logicle_params;
	p->taylor = 0;

	if (T <= 0)
		throw IllegalParameter("T is not positive");
	if (W < 0)
		throw IllegalParameter("W is negative");
	if (M <= 0)
		throw IllegalParameter("M is not positive");
	if (2 * W > M)
		throw IllegalParameter("W is too large");
	if (-A > W || A + W > M - W)
		throw IllegalParameter("A is too large");

	// if we're going to bin the data make sure that
	// zero is on a bin boundary by adjusting A
	if (bins > 0)
	{
		double zero = (W + A) / (M + A);
		zero = floor(zero * bins + .5) / bins;
		A = (M * zero - W) / (1 - zero);
	}

	// standard parameters
	p->T = T;
	p->M = M;
	p->W = W;
	p->A = A;

	// actual parameters
	// formulas from biexponential paper
	p->w = W / (M + A);
	p->x2 = A / (M + A);
	p->x1 = p->x2 + p->w;
	p->x0 = p->x2 + 2 * p->w;
	p->b = (M + A) * LN_10;
	p->d = solve(p->b, p->w);
	double c_a = exp(p->x0 * (p->b + p->d));
	double mf_a = exp(p->b * p->x1) - c_a / exp(p->d * p->x1);
	p->a = T / ((exp(p->b) - mf_a) - c_a / exp(p->d));
	p->c = c_a * p->a;
	p->f = -mf_a * p->a;

	// use Taylor series near x1, i.e., data zero to
	// avoid round off problems of formal definition
	p->xTaylor = p->x1 + p->w / 4;
	// compute coefficients of the Taylor series
	double posCoef = p->a * exp(p->b * p->x1);
	double negCoef = -p->c / exp(p->d * p->x1);
	// 16 is enough for full precision of typical scales
	p->taylor = new double[TAYLOR_LENGTH];
	for (int i = 0; i < TAYLOR_LENGTH; ++i)
	{
		posCoef *= p->b / (i + 1);
		negCoef *= -p->d / (i + 1);
		(p->taylor)[i] = posCoef + negCoef;
	}
	p->taylor[1] = 0; // exact result of Logicle condition
}

Logicle::Logicle (double T, double W, double M, double A)
{
	initialize(T, W, M, A, 0);
}

Logicle::Logicle (double T, double W, double M, double A, int bins)
{
	initialize(T, W, M, A, bins);
}

Logicle::Logicle (const Logicle & logicle)
{
	p = new logicle_params;
	memcpy(p, logicle.p, sizeof(logicle_params) );
	p->taylor = new double[TAYLOR_LENGTH];
	memcpy(p->taylor, logicle.p->taylor, TAYLOR_LENGTH * sizeof(double));
}

Logicle::~Logicle ()
{
	delete p->taylor;
	delete p;
}

double Logicle::solve (double b, double w)
{
	// w == 0 means its really arcsinh
	if (w == 0)
		return b;

	// precision is the same as that of b
	double tolerance = 2 * b * EPSILON;

	// based on RTSAFE from Numerical Recipes 1st Edition
	// bracket the root
	double d_lo = 0;
	double d_hi = b;

	// bisection first step
	double d = (d_lo + d_hi) / 2;
	double last_delta = d_hi - d_lo;
	double delta;

	// evaluate the f(w,b) = 2 * (ln(d) - ln(b)) + w * (b + d)
	// and its derivative
	double f_b = -2 * log(b) + w * b;
	double f = 2 * log(d) + w * d + f_b;
	double last_f = NaN;

	for (int i = 1; i < 20; ++i)
	{
		// compute the derivative
		double df = 2 / d + w;

		// if Newton's method would step outside the bracket
		// or if it isn't converging quickly enough
		if (((d - d_hi) * df - f) * ((d - d_lo) * df - f) >= 0
			|| std::abs(1.9 * f) > std::abs(last_delta * df))
		{
			// take a bisection step
			delta = (d_hi - d_lo) / 2;
			d = d_lo + delta;
			if (d == d_lo)
				return d; // nothing changed, we're done
		}
		else
		{
			// otherwise take a Newton's method step
			delta = f / df;
			double t = d;
			d -= delta;
			if (d == t)
				return d; // nothing changed, we're done
		}
		// if we've reached the desired precision we're done
		if (std::abs(delta) < tolerance)
			return d;
		last_delta = delta;

		// recompute the function
		f = 2 * log(d) + w * d + f_b;
		if (f == 0 || f == last_f)
			return d; // found the root or are not going to get any closer
		last_f = f;

		// update the bracketing interval
		if (f < 0)
			d_lo = d;
		else
			d_hi = d;
	}

	throw DidNotConverge("exceeded maximum iterations in solve()");
}

double Logicle::slope (double scale) const
{
	// reflect negative scale regions
	if (scale < p->x1)
		scale = 2 * p->x1 - scale;

	// compute the slope of the biexponential
	return p->a * p->b * exp(p->b * scale) + p->c * p->d / exp(p->d * scale);
}

double Logicle::seriesBiexponential (double scale) const
{
	// Taylor series is around x1
	double x = scale - p->x1;
	// note that taylor[1] should be identically zero according
	// to the Logicle condition so skip it here
	double sum = p->taylor[TAYLOR_LENGTH - 1] * x;
	for (int i = TAYLOR_LENGTH - 2; i >= 2; --i)
		sum = (sum + p->taylor[i]) * x;
	return (sum * x + p->taylor[0]) * x;
}

double Logicle::scale (double value) const
{
	// handle true zero separately
	if (value == 0)
		return p->x1;

	// reflect negative values
	bool negative = value < 0;
	if (negative)
		value = -value;

	// initial guess at solution
	double x;
	if (value < p->f)
		// use linear approximation in the quasi linear region
		x = p->x1 + value / p->taylor[0];
	else
		// otherwise use ordinary logarithm
		x = log(value / p->a) / p->b;

	// try for double precision unless in extended range
	double tolerance = 3 * EPSILON;
	if (x > 1)
		tolerance = 3 * x * EPSILON;

	for (int i = 0; i < 10; ++i)
	{
		// compute the function and its first two derivatives
		double ae2bx = p->a * exp(p->b * x);
		double ce2mdx = p->c / exp(p->d * x);
		double y;
		if (x < p->xTaylor)
			// near zero use the Taylor series
			y = seriesBiexponential(x) - value;
		else
			// this formulation has better roundoff behavior
			y = (ae2bx + p->f) - (ce2mdx + value);
		double abe2bx = p->b * ae2bx;
		double cde2mdx = p->d * ce2mdx;
		double dy = abe2bx + cde2mdx;
		double ddy = p->b * abe2bx - p->d * cde2mdx;

		// this is Halley's method with cubic convergence
		double delta = y / (dy * (1 - y * ddy / (2 * dy * dy)));
		x -= delta;

		// if we've reached the desired precision we're done
		if (std::abs(delta) < tolerance)
			// handle negative arguments
			if (negative)
				return 2 * p->x1 - x;
			else
				return x;
	}

	throw DidNotConverge("scale() didn't converge");
};

double Logicle::inverse (double scale) const
{
	// reflect negative scale regions
	bool negative = scale < p->x1;
	if (negative)
		scale = 2 * p->x1 - scale;

	// compute the biexponential
	double inverse;
	if (scale < p->xTaylor)
		// near x1, i.e., data zero use the series expansion
		inverse = seriesBiexponential(scale);
	else
		// this formulation has better roundoff behavior
		inverse = (p->a * exp(p->b * scale) + p->f) - p->c / exp(p->d * scale);

	// handle scale for negative values
	if (negative)
		return -inverse;
	else
		return inverse;
};

double Logicle::dynamicRange () const
{
	return slope(1) / slope(p->x1);
};

void Logicle::axisLabels (std::vector<double> & label) const
{
	// number of decades in the positive logarithmic region
	double pd = p->M - 2 * p->W;
	// smallest power of 10 in the region
	double log10x = ceil(log(p->T) / LN_10 - pd);
	// data value at that point
	double x = exp(LN_10 * log10x);
	// number of positive labels
	int np;
	if (x > p->T)
	{
		x = p->T;
		np = 1;
	}
	else
		np = (int) (floor(log(p->T) / LN_10 - log10x)) + 1;
	// bottom of scale
	double B = this->inverse(0);
	// number of negative labels
	int nn;
	if (x > -B)
		nn = 0;
	else if (x == p->T)
		nn = 1;
	else
		nn = (int) floor(log(-B) / LN_10 - log10x) + 1;

	// fill in the axis labels
	label.resize(nn + np + 1);
	label[nn] = 0;
	for (int i = 1; i <= nn; ++i)
	{
		label[nn - i] = -x;
		label[nn + i] = x;
		x *= 10;
	}
	for (int i = nn + 1; i <= np; ++i)
	{
		label[nn + i] = x;
		x *= 10;
	}
}

// Visual C++ hack!
int PullInMyLibrary () { return 0; };
