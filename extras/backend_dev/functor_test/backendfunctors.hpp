//  GAMBIT: Global and Modular BSM Inference Tool
//  *********************************************
//
//  Backend functor class definitions.
//
//  *********************************************
//
//  Authors
//  =======
//
//  (add name and date if you modify)
//
//  Anders Kvellestad 
//  2013  Apr 14  --> Added alternatice backend functor class
//
//  Pat Scott
//  2013  Apr 4++
//  *********************************************

#ifndef __functors_hpp__
#define __functors_hpp__

#include <string>
#include <vector>
#include <map>
#include <algorithm>

namespace GAMBIT
{

  // A container for a function that needs to be constructed at compile
  // and executed as initialisation code at startup.
  struct ini_code
  {
    ini_code(void (*unroll)()) { (*unroll)(); }
  };


  // Function wrapper (functor) base class
  class functor
  {

    public:

      typedef std::string str;
      typedef std::pair<str, str> sspair;

      // Empty virtual destructor to make polymorphic
      virtual ~functor() {}

      // It may be safer to have the following things accessible 
      // only to the likelihood wrapper class and/or dependency resolver, i.e. so they cannot be used 
      // from within module functions

      // Identification methods
      str name()        { return myName;       }
      str capability()  { return myCapability; }
      str type()        { return myType;       }
      str origin()      { return myOrigin;     }
      str version()     { return myVersion;    }
      sspair quantity() { return std::make_pair(myCapability, myType); }

      // Set method for version
      void setVersion(str ver) { myVersion = ver; }

      // Getters for unconditional dependencies, backend requirements and permitted backends
      std::vector<sspair> dependencies()                  { return myDependencies; }
      std::vector<sspair> backendreqs()                   { return myBackendReqs; }
      std::vector<sspair> backendspermitted(sspair quant) 
      { 
        if (permitted_map.find(quant) != permitted_map.end())
        {
          return permitted_map[quant]; 
        }
        else
        {
          std::vector<sspair> empty;
          return empty;
        }
      }

      // Getter for backend-specific conditional dependencies (4-string version)
      std::vector<sspair> backend_conditional_dependencies (str req, str type, str be, str ver)  
      { 
        std::vector<sspair> generic_deps;
        std::vector<sspair> specific_deps;
        std::vector<sspair> total_deps;
        std::vector<str> quad;
        quad.push_back(req);
        quad.push_back(type);
        quad.push_back(be);
        quad.push_back(ver);
        //Check first what conditional dependencies exist for all versions of this backend
        if (ver != "any")
        {
          generic_deps = backend_conditional_dependencies(req, type, be, "any");
        }
        //Now see if there are any for this specific version
        if (myBackendConditionalDependencies.find(quad) != myBackendConditionalDependencies.end())
        {
          specific_deps = myBackendConditionalDependencies[quad];
        }
        //Now put them together
        total_deps.reserve(generic_deps.size() + specific_deps.size());
        total_deps.insert(total_deps.end(), generic_deps.begin(), generic_deps.end());
        total_deps.insert(total_deps.end(), specific_deps.begin(), specific_deps.end());        
        return total_deps;
      }
      
      // Getter for backend-specific conditional dependencies (3-string version)
      std::vector<sspair> backend_conditional_dependencies (str req, str type, str be)  
      { 
        return backend_conditional_dependencies(req, type, be, "any");
      }
      
      // Getter for backend-specific conditional dependencies (backend functor pointer version)
      std::vector<sspair> backend_conditional_dependencies (functor* be_functor)  
      { 
        return backend_conditional_dependencies (be_functor->capability(), be_functor->type(),
         be_functor->origin(), be_functor->version());
      }

      // Getter for model-specific conditional dependencies
      std::vector<sspair> model_conditional_dependencies (str model)
      { 
        if (myModelConditionalDependencies.find(model) != myModelConditionalDependencies.end())
        {
          return myModelConditionalDependencies[model];
        }
        else
        {
          std::vector<sspair> empty;
          return empty;
        }
      }

      // Needs recalculating or not?  (Externally modifiable)
      bool needs_recalculating;

      // Resolve a dependency using a pointer to another functor object
      void resolveDependency (functor* dep_functor)
      {
        sspair key (dep_functor->quantity());
        if (dependency_map.find(key) == dependency_map.end())                            
        {                                                                      
          std::cout << "Error whilst attempting to resolve dependency:" << std::endl;
          std::cout << "Function "<< myName << " in " << myOrigin << " does not depend on " << std::endl;
          std::cout << "capability " << key.first << " with type " << key.second << "." << std::endl;
          //FIXME throw a real error here
        }
        else { (*dependency_map[key])(dep_functor); }
      }

      // Resolve a backend requirement using a pointer to another functor object
      void resolveBackendReq (functor* be_functor)
      {
        sspair key (be_functor->quantity());
        //First make sure that the proposed backend function fulfills a known requirement of the module function.
        if (backendreq_map.find(key) != backendreq_map.end())                            
        { 
          sspair proposal (be_functor->origin(), be_functor->version());  //Proposed backend-version pair
          sspair generic_proposal (be_functor->origin(), "any");          //Proposed backend, any version 
          if ( //Check for a condition under which the proposed backend function is an acceptable fit for this requirement.
           //Check whether there are have been any permitted backends stated for this requirement (if not, anything goes).
           (permitted_map.find(key) == permitted_map.end()) || 
           //Iterate over the vector of backend-version pairs for this requirement to see if all versions of the 
           //proposed backend have been explicitly permitted.
           (std::find(permitted_map[key].begin(), permitted_map[key].end(), generic_proposal) != permitted_map[key].end()) ||
           //Iterate over the vector of backend-version pairs again to see if the specific backend version 
           //proposed had been explicitly permitted.
           (std::find(permitted_map[key].begin(), permitted_map[key].end(), proposal) != permitted_map[key].end()) )         
          {
            (*backendreq_map[key])(be_functor);   //One of the conditions was met, so do the resolution
          }
          else          
          { 
            std::cout << "Error whilst attempting to resolve backend requirement:" << std::endl;
            std::cout << "Backend capability " << key.first << " with type " << key.second << "." << std::endl;
            std::cout << "required by function "<< myName << " in " << myOrigin << " is not permitted " << std::endl;
            std::cout << "to use "<< proposal.first << ", version " << proposal.second << "." << std::endl;
            //FIXME throw a real error here
          } 
        }
        else
        {                                                                      
          std::cout << "Error whilst attempting to resolve backend requirement:" << std::endl;
          std::cout << "Function "<< myName << " in " << myOrigin << " does not require " << std::endl;
          std::cout << "backend capability " << key.first << " with type " << key.second << "." << std::endl;
          //FIXME throw a real error here
        }        
      }

    protected:
                        //Internal storage of
      str myName;       //the function name,
      str myCapability; //exactly what it calculates,
      str myType;       //the type of what it calculates,
      str myOrigin;     //the name of the module or backend to which it belongs,
      str myVersion;    //and the module/backend version number or string.

      std::vector<sspair> myDependencies;        // Vector of dependency-type pairs as strings 
      std::vector<sspair> myBackendReqs;         // Vector of backend requirement-type pairs as strings

      // Map from (vector with 4 strings: backend req, type, backend, version) to (vector of {conditional dependency-type} pairs)
      std::map< std::vector<str>, std::vector<sspair> > myBackendConditionalDependencies;

      // Map from models to (vector of {conditional dependency-type} pairs)
      std::map< str, std::vector<sspair> > myModelConditionalDependencies;

      // Map from backend requirements to their required types
      std::map<str, str> backendreq_types;

      // Map from (dependency-type pairs) to (pointers to templated void functions 
      // that set dependency functor pointers)
      std::map<sspair, void(*)(functor*)> dependency_map;

      // Map from (backend requirement-type pairs) to (pointers to templated void functions 
      // that set backend requirement functor pointers)
      std::map<sspair, void(*)(functor*)> backendreq_map;

      // Map from (backend requirement-type pairs) to (vector of permitted {backend-version} pairs)
      std::map< sspair, std::vector<sspair> > permitted_map;

  };


  // Functor derived class for functions with result type TYPE
  template <typename TYPE>
  class typed_functor : public functor
  {

    public:

      typedef functor::str str;

      // Constructor 
      typed_functor(void (*inputFunction)(TYPE &), 
                           str func_name,
                           str func_capability, 
                           str result_type,
                           str origin_name)
      {
        std::cout << "functor initialization: " << func_name << std::endl;
        myFunction      = inputFunction;
        myName          = func_name;
        myCapability    = func_capability;
        myType          = result_type;
        myOrigin        = origin_name;
        needs_recalculating = true;
      }

      // Calculate method
      void calculate() { if(needs_recalculating) { myFunction(myValue); } }

      // Operation (return value) 
      TYPE operator()() { return myValue; }

    protected:

      // Internal storage of function value
      TYPE myValue;

      // Internal storage of function pointer
      void (*myFunction)(TYPE &);

  };


  // Functor derived class for module functions with result type TYPE
  template <typename TYPE>
  class module_functor : public typed_functor<TYPE>
  {

    public:

      typedef functor::str str;
      typedef functor::sspair sspair;

      // Constructor: call typed_functor constructor
      module_functor(void (*inputFunction)(TYPE &), 
                            str func_name,
                            str func_capability, 
                            str result_type,
                            str origin_name) 
      : typed_functor<TYPE>(inputFunction, func_name, func_capability, result_type, origin_name) {}

      // Add a dependency (a beer for anyone who can explain why this-> is required here)
      void setDependency(str dep, str type, void(*resolver)(functor*))
      { 
        sspair key (dep, type);
        this->myDependencies.push_back(key);
        this->dependency_map[key] = resolver;
      }

      // Add a backend conditional dependency
      void setBackendConditionalDependency
       (str req, str be, str ver, str dep, str dep_type, void(*resolver)(functor*))
      { 
        sspair key (dep, dep_type);
        std::vector<str> quad;
        if (this->backendreq_types.find(req) != this->backendreq_types.end())
        {
          quad.push_back(req);
          quad.push_back(this->backendreq_types[req]);
          quad.push_back(be);
          quad.push_back(ver);
        }
        else
        {
          std::cout << "Error whilst attempting to set backend-conditional dependency:" << std::endl;
          std::cout << "The type of the backend requirement " << req << "on which the " << std::endl; 
          std::cout << "dependency "<< dep << " is conditional has not been set.  This" << std::endl;
          std::cout << "is " << this->name() << " in " << this->origin() << "." << std::endl;
          //FIXME throw a real error here
        }
        if (this->myBackendConditionalDependencies.find(quad) == this->myBackendConditionalDependencies.end())
        {
          std::vector<sspair> newvec;
          this->myBackendConditionalDependencies[quad] = newvec;
        }
        this->myBackendConditionalDependencies[quad].push_back(key);
        this->dependency_map[key] = resolver;
      }

      // Add a model conditional dependency
      void setModelConditionalDependency
       (str model, str dep, str dep_type, void(*resolver)(functor*))
      { 
        sspair key (dep, dep_type);
        if (this->myModelConditionalDependencies.find(model) == this->myModelConditionalDependencies.end())
        {
          std::vector<sspair> newvec;
          this->myModelConditionalDependencies[model] = newvec;
        }
        this->myModelConditionalDependencies[model].push_back(key);
        this->dependency_map[key] = resolver;
      }

      // Add a backend requirement
      void setBackendReq(str req, str type, void(*resolver)(functor*))
      { 
        sspair key (req, type);
        this->backendreq_types[req] = type;
        this->myBackendReqs.push_back(key);
        this->backendreq_map[key] = resolver;
      }

      // Add a permitted backend
      void setPermittedBackend(str req, str be, str ver)
      { 
        sspair key;
        if (this->backendreq_types.find(req) != this->backendreq_types.end())
        {
          key = std::make_pair(req, this->backendreq_types[req]);
        }
        else
        {
          std::cout << "Error whilst attempting to set permitted backend:" << std::endl;
          std::cout << "The return type of the backend requirement " << req << "is not set." << std::endl; 
          std::cout << "This is " << this->name() << " in " << this->origin() << "." << std::endl;
          //FIXME throw a real error here
        }
        sspair vector_entry (be,  ver);
        if (this->permitted_map.find(key) == this->permitted_map.end())
        {
          std::vector<sspair> newvec;
          this->permitted_map[key] = newvec;
        }
        this->permitted_map[key].push_back(vector_entry);
        std::vector<sspair> temp2;	
        temp2 = this->permitted_map[key];
        std::cout<<"in setpermittedbe: "<<temp2[0].first<<"  "<<temp2[0].second<<std::endl;
        
      }

    protected:

  };


  // Functor derived class for backend functions with result type TYPE
  template <typename TYPE>
  class backend_functor : public typed_functor<TYPE>
  {

    public:

      typedef functor::str str;

      // Constructor: call typed_functor constructor
      backend_functor(void (*inputFunction)(TYPE &), 
                             str func_name,
                             str func_capability, 
                             str result_type,
                             str origin_name,
                             str origin_version) 
      : typed_functor<TYPE>(inputFunction, func_name, func_capability, result_type, origin_name) 
      {
        this->setVersion(origin_version);
      }

      // Method for passing input parameters to backend functions !FIXME not finished
      void give_input() { }

    protected:

  };





  // ==================================================================


  /* ----------------------------------------
   * Backend functor class for functions with 
   * result type TYPE and argumentlist ARGS 
   * ---------------------------------------- */

  /* Based on:
   * http://stackoverflow.com/questions/9050047/generic-functor-for-functions-with-any-argument-list/9050114#9050114 */

  template <typename TYPE, typename... ARGS>
  class backend_functor2 : public functor
  {

    public:

      typedef functor::str str;

      /* Constructor */ 
      backend_functor2(  std::function<TYPE(ARGS...)> inputFunction, 
                           str func_name,
                           str func_capability, 
                           str result_type,
                           str origin_name,
                           str origin_version)
      {
        std::cout << "functor initialization: " << func_name << std::endl;
        
        myFunction      = inputFunction;
        myName          = func_name;
        myCapability    = func_capability;
        myType          = result_type;
        myOrigin        = origin_name;
        myVersion       = origin_version;
        needs_recalculating = true;
      }

      /* Which is the better user interface?
       * 
       * 1) Force the use of 'someFunctor.calculate(args...)'
       *    to run a calculation and then obtain result via 'someFunctor()'.
       * 
       * 2) Use 'someFunctor(args...)' to perform calculation and return result.
       *    The function 'someFunctor.calculate(args...)' could still be used
       *    to force a re-calculation (regardless of 'needs_recalculating' flag).
       *    (Could also throw in a 'getResult()' function.) */
       
      // 1) Calculate method
      //void calculate(ARGS... args) { if(needs_recalculating) { myValue = myFunction(args...); } }

      // 1) Operation (return value) 
      //TYPE operator()() { return myValue; }

      // 2) Calculate method 
      void calculate(ARGS... args) { myValue = myFunction(args...); }

      // 2) Operation (execute function and return value) 
      TYPE operator()(ARGS... args) 
      { 
        if(needs_recalculating) { myValue = myFunction(args...); }
        return myValue;
      }


    protected:

      // Internal storage of wrapped function
      std::function<TYPE(ARGS...)> myFunction;

      // Internal storage of function value
      TYPE myValue;
  };




  /* ---------------------------------------
   * Specialization of backend functor class 
   * for functions with result type void
   * --------------------------------------- */
  template <typename... ARGS>
  class backend_functor2<void, ARGS...> : public functor
  {

    public:

      typedef functor::str str;

      // Constructor 
      backend_functor2(  std::function<void(ARGS...)> inputFunction, 
                           str func_name,
                           str func_capability, 
                           str result_type,
                           str origin_name,
                           str origin_version)
      {
        std::cout << "functor initialization: " << func_name << std::endl;
        
        myFunction      = inputFunction;
        myName          = func_name;
        myCapability    = func_capability;
        myType          = result_type;
        myOrigin        = origin_name;
        myVersion       = origin_version;
        needs_recalculating = true;
      }

      /* Which is the better user interface?
       * (specialized for void return type)
       *
       * 1) Force the use of 'someFunctor.calculate(args...)'.
       *
       * 2) Use 'someFunctor(args...)' to perform calculation.
       *    The function 'someFunctor.calculate(args...)' could still be used
       *    to force a re-calculation (regardless of 'needs_recalculating' flag). */

      // 1) Calculate method
      //void calculate(ARGS... args) { if(needs_recalculating) { myFunction(args...); } }

      // 2) Calculate method 
      void calculate(ARGS... args) { myFunction(args...); }

      // 2) Operation (execute function and return value) 
      void operator()(ARGS... args) { if(needs_recalculating) { myFunction(args...); } }


    protected:

      // Internal storage of wrapped function
      std::function<void(ARGS...)> myFunction;
  };




  /* -------------------------------------------
   * Templated function for creating an instance 
   * of the class 'backend_functor2' 
   * ------------------------------------------- */
  template<typename OUTTYPE, typename... ARGS>
  backend_functor2<OUTTYPE,ARGS...> makeBackendFunctor( OUTTYPE(*f_in)(ARGS...), 
                                                          std::string func_name, 
                                                          std::string func_capab, 
                                                          std::string ret_type, 
                                                          std::string origin_name,
                                                          std::string origin_ver) 
  { 
    return backend_functor2<OUTTYPE,ARGS...>(f_in, func_name,func_capab,ret_type,origin_name,origin_ver);
  }



}

#endif /* defined(__functors_hpp__) */