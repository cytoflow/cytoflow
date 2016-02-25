#include "logicle.h"
#include <memory.h>
#include <cmath>

const int FastLogicle::DEFAULT_BINS = 1 << 12;

void FastLogicle::initialize (int bins)
{
	p->bins = bins;
	p->lookup = new double[bins + 1];
	for (int i = 0; i <= bins; ++i)
		p->lookup[i] = Logicle::inverse((double)i / (double) bins);
}

FastLogicle::FastLogicle (double T, double W, double M, double A, int bins)
	: Logicle(T, W, M, A, bins)
{
	initialize(bins);
}

FastLogicle::FastLogicle (double T, double W, double M, int bins)
: Logicle(T, W, M, 0, bins)
{
	initialize(bins);
}

FastLogicle::FastLogicle (double T, double W, int bins)
: Logicle(T, W, DEFAULT_DECADES, 0, bins)
{
	initialize(bins);
}

FastLogicle::FastLogicle (double T, double W, double M, double A)
: Logicle(T, W, M, A, DEFAULT_BINS)
{
	initialize(DEFAULT_BINS);
}

FastLogicle::FastLogicle (double T, double W, double M)
: Logicle(T, W, M, 0, DEFAULT_BINS)
{
	initialize(DEFAULT_BINS);
}

FastLogicle::FastLogicle (double T, double W)
: Logicle(T, W, DEFAULT_DECADES, 0, DEFAULT_BINS)
{
	initialize(DEFAULT_BINS);
}

FastLogicle::FastLogicle (const FastLogicle & logicle) : Logicle(logicle)
{
	p->bins = logicle.p->bins;
	p->lookup = new double[p->bins + 1];
	memcpy(p->lookup, logicle.p->lookup, (p->bins + 1) * sizeof (double));
}

FastLogicle::~FastLogicle ()
{
	delete p->lookup;
}

int FastLogicle::intScale (double value) const
{
    // binary search for the appropriate bin
    int lo = 0;
    int hi = p->bins;
    while (lo <= hi)
    {
      int mid = (lo + hi) >> 1;
      double key = p->lookup[mid];
      if (value < key)
        hi = mid - 1;
      else if (value > key)
        lo = mid + 1;
      else if (mid < p->bins)
        return mid;
      else
        // equal to table[bins] which is for interpolation only
		throw IllegalArgument(value);
	}

    // check for out of range
    if (hi < 0 || lo > p->bins)
		throw IllegalArgument(value);

    return lo - 1;
}

double FastLogicle::scale (double value) const
{
    // lookup the nearest value
    int index = intScale(value);

    // inverse interpolate the table linearly
    double delta = (value - p->lookup[index])
      / (p->lookup[index + 1] - p->lookup[index]);

    return (index + delta) / (double)p->bins;
}

double FastLogicle::inverse (double scale) const
{
    // find the bin
    double x = scale * p->bins;
    int index = (int)floor(x);
    if (index < 0 || index >= p->bins)
		throw IllegalArgument(scale);

    // interpolate the table linearly
    double delta = x - index;

    return (1 - delta) * p->lookup[index] + delta * p->lookup[index + 1];
}

double FastLogicle::inverse (int index) const
{
    if (index < 0 || index >= p->bins)
		throw IllegalArgument(index);

    return p->lookup[index];
}
