/*! \file 
*/

//ZStepper_SDK.h

#ifdef __cplusplus
extern "C" 
{
#endif

/*! \enum Params Device parameter settings*/
	enum Params
	{
		PARAM_FIRST_PARAM,
		PARAM_DEVICE_TYPE=0,
		PARAM_Z_POS = 400,///<Absolute location for Z
		PARAM_Z_ZERO = 402,///<Set the current location to zero. The device will read zero for postion after this parameter is set
		PARAM_Z_STEPS_PER_MM = 403,///<Set the number of steps per millimeter. This is dependent on the know the stepper is connected to.
		PARAM_Z_VELOCITY = 404,///<The speed to move the stepper at
		PARAM_LAST_PARAM
	};

/*! \enum ParamType data of the parameter*/
	enum ParamType
	{
		TYPE_LONG,///<Parameter is of type integer
		TYPE_DOUBLE///<Parameter is of type double precision floating point
	};

/*! \enum DeviceType Type of the device returned by PARAM_DEVICE_TYPE*/
	enum DeviceType
	{
		DEVICE_TYPE_FIRST,
		STAGE_Z=0x10,
		DEVICE_TYPE_LAST
	};

/*! \enum StatusType return value for the StatusAcquisition status variable*/
	enum StatusType
	{
		STATUS_BUSY=0,///<Camera is busy capturing an image(s)
		STATUS_READY,///<Camera is idle or has completed capturing an image(s)
		STATUS_ERROR///<Error occuring during the capture. Error flag will persist until a new capture is setup.
	};


/*! \fn long FindDevices(long &DeviceCount)
    \brief Locates connected devices.
    \param DeviceCount The number of devices currently available
	\return If the function succeeds the return value is TRUE. 	
*/
	long FindDevices(long &DeviceCount);


/*! \fn long SelectDevice(const long device)
    \brief Selects an available device
    \param device zero based index of a device
	\return If the function succeeds the return value is TRUE. All parameters and actions are directed the selected device. 
*/	  
long SelectDevice(const long Device);


/*! \fn long TeardownDevice
    \brief Release resources associated with the device before shutting down the application
	\return If the function succeeds the return value is TRUE and the device shutdown normally.
*/
long TeardownDevice();

/*! \fn long GetParamInfo(const long paramID, long &paramType, long &paramAvailable, long &paramReadOnly, double &paramMin, double &paramMax, double &paramDefault)
    \brief  Retrieve parameter information and capabilities
    \param paramID Unique identifier for the parameter to interrogate
	\param paramType The ParamType for the paramID
	\param paramAvailable Returns TRUE if the paramID is supported
	\param paramReadOnly Returns TRUE if the paramID can only be read
	\param paramMin Minimum value for the paramID
	\param paramMax Maximum value for the param ID
	\param paramDefault Recommended default for the paramID
	\return If the function succeeds the return value is TRUE.
*/
long GetParamInfo(const long paramID, long &paramType, long &paramAvailable, long &paramReadOnly, double &paramMin, double &paramMax, double &paramDefault);

/*! \fn long SetParam(const long paramID, const double param)
    \brief Sets a parameter value
	\param paramID Unique ID of the parameter to set.
    \param param Input value. If the Paramtype is long the data must be cast to type double.
	\return If the function succeeds the return value is TRUE.
	\example PositionTest.cpp
*/
long SetParam(const long paramID, const double param);

/*! \fn long GetParam(const long paramID, double &param)
    \brief Gets a parameter value
	\param paramID Unique ID of the parameter to retrieve
    \param param Current value of the parameter
	\return If the function succeeds the return value is TRUE.
	\example PositionTest.cpp
*/
long GetParam(const long paramID, double &param);


/*! \fn long PreflightPosition()
    \brief Using the current parameters arm the camera for a single/series capture
  	\return If the function succeeds the return value is TRUE.
*/
long PreflightPosition();///<This submits the current parameters to the Device. There may be some first time latencey in settings parameters so its best to call this outside of the shutter control for image capture

/*! \fn long SetupPosition()
    \brief Using the current parameters the device is armed for the next capture
 	\return If the function succeeds the return value is TRUE.
*/
long SetupPosition();///<This submits the parameters that can chage while the Device is active. 


/*! \fn long StartPosition()
    \brief If not already started begin an image capture.
	\return If the function succeeds the return value is TRUE.
*/
long StartPosition();///<Begin the capture.

/*! \fn long StatusPosition(long &status)
    \brief Determine the capture status of the current image capture
    \param status Returns the status of the current capture. See StatusType.
	\return If the function succeeds the return value is TRUE.
*/
long StatusPosition(long &status);///<returns the status of the capture


/*! \fn long ReadPosition(DeviceType deviceType, double &pos)
    \brief Read the current location from the device. This may not equal the last position sent to the device if the device is moved manually.
	\return If the function succeeds the return value is TRUE.
*/
long ReadPosition(DeviceType deviceType, double &pos);


/*! \fn long PostflightPosition()
    \brief Releases any resources after a series of images have been captured
	\return If the function succeeds the return value is TRUE.	
*/
long PostflightPosition();


/*! \fn long GetLastErrorMsg(wchar_t * msg, long size)
    \brief Retrieve the last error message
    \param msg user allocated buffer for storing the error message
	\param size of the buffer (in characters) of the buffer provided
	\return If the function succeeds the return value is TRUE.	
*/
long GetLastErrorMsg(wchar_t *msg, long size);


#ifdef __cplusplus
}
#endif
