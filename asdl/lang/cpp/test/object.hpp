#ifndef OBJECT_H
#define OBJECT_H

#include <iostream>
#include <string>


int var = 0;
int tab[3] = {1,2,3};

namespace N {
template <typename T, typename S>
class Object
{
public:
  Object(int i = 3) : m_i(i) {}
  // namespace is mandatory in the example because it is present in the AST
  Object(const N::Object<T,S>& o);

  virtual ~Object();

  // int run(bool b);
  int run(bool b)
  {
    switch (m_i)
    {
      case 0:
        return b;
        break;
      default:
        return !b;
    }
    std::string s = "azer";
    if (b)
      return 0;
    else
    {
      float f1 = 0.11;
      std::cerr << s << " " << b << std::endl;
      return 1;
    }
  }
private:
  int m_i = 23;
};
}

using namespace N;
int n = 2;

int f(int p=3)
{
  char c = 'c';
  c = c+2;
//   c += 1;
  return (p+1)*2;
}

#endif
