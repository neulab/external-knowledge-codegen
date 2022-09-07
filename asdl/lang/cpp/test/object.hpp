#ifndef OBJECT_H
#define OBJECT_H

#include <iostream>
#include <string>

class Object {
public:
  int run(bool b)
  {
    std::string s = "azer";
    if (b)
      return 0;
    else
    {
      float f0;
      float f1 = 0.11;
//       std::cerr << s << " " << b << std::endl;
      return 1;
    }
  }
};

#endif
