#ifndef OBJECT_H
#define OBJECT_H

// #include <iostream>
// #include <string>

class Object
{
public:
  Object(int i = 3) : m_i(i) {}
  virtual ~Object();

//   int run(bool b)
//   {
//     std::string s = "azer";
//     if (b)
//       return 0;
//     else
//     {
//       float f1 = 0.11;
// //       std::cerr << s << " " << b << std::endl;
//       return 1;
//     }
//   }
private:
  int m_i = 23;
};

#endif
