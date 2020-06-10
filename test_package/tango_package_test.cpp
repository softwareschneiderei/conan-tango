#include <tango.h>
#include <dserver.h>

int main()
{
    volatile int never = 0;
    if (never != 0)
    {
        // Just link, but never run
        Tango::DServer instance(nullptr, nullptr, nullptr, Tango::ON, nullptr);
    }
    return 0;
}
