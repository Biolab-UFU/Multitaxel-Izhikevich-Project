#include "filter.h"
#include "mbed.h"
#include "electrode.h"

/********************/
/* Global Variables */
/********************/
#define GAIN_VALUE (.1)
#define NOTCH_N     (2)   // The number of cascaded second-order filters 
                        // making up the notch filter 
#define NOTCH_Q     (31)  // The  number of fractional bits in 
                        // the notch filter coefficients
#define SPIKE_CUTOFF_MAX (25000) // The maximum output of human EMG
#define SPIKE_CUTOFF_MIN (-25000) // The maximum output of human EMG

typedef struct 
{
    /* Variables to implement the high pass filter */
    int prev_result; // y[n-1]]
    int hpf_input_prev; // x[n-1]]

    /* Variables used to implement the notch filter */
    long long s_notch[NOTCH_N][2];    // notch filter internal 
                                    // states must be held
                                    // in memory in between 
                                    // calls to the filter  
    int b_notch[NOTCH_N][3];
    int a_notch[NOTCH_N][2];
    int integral;
    int resultPrev;
  
} Filter_t;

Filter_t instance[MAX_ELECTRODES];

/*                      */
/*  Private Functions   */
/*                      */

/********************************************************************/
/* First order butterworth filter                                   */
/* implements the equations:                                        */
/* y[i] = b_0*x[i] + b_1*x[i-1] - a_1*y[i-1]                        */
/* Filter coefficients obtained with the following lines in MATLAB  */
/* Fc = 10;                                                         */
/* Fs = 1e3;                                                        */
/* N = 32;                                                          */
/* [bhat,ahat] = butter(1,Fc/(Fs/2),'high');                        */
/* b = round(bhat*2^(N-1));                                         */
/* a = round(ahat*2^(N-1));                                         */
/* Since b_0 = -1*b_1 we only store a single coefficient below      */
/* Note: coefficients derived when using 3kHz sampling, with 1 kHz  */
/* sampling rate Fc becomes 10/3, which is still acceptable         */
/* for baseline drift removal                                       */
/********************************************************************/
int HighPass_filter_IIR(int new_data,int prev_data, int prev_output)
{    
    //cutoff = 10Hz
    int b =  2082052512;
    int a = -2016621376;
	
	//cutoff = 15Hz
	//int b =  2050771709;
	//int a = -1954059770;
	
	//cutoff = 20Hz
	//int b =  2020372579;
	//int a = -1893261511;

    int delta;
    long long in_prod;
    long long out_prod;
    long long yM;
    int y;
    delta = new_data-prev_data;
    in_prod = (long long) b*delta;
    out_prod = (long long) a*prev_output;
    yM = in_prod - out_prod;
    y = yM >> 31;

    return(y);
}


/************************************************************************/    
/* 4th Order IIR notch filter implemented as a cascade of "NOTCH_N"     */
/* biquad (2nd order) filters in Transposed-Direct-Form-II              */
/* Each stage satisfies the following equation:                         */
/* y[n] = b_0*x[n] + b_1*x[n-1] + b_2*x[n-2] - a_1*y[n-1] - a_2*y[n-2]  */
/* Filter coefficients obtained with the following lines in MATLAB:     */
/* Fs = 1e3;   % sampling frequency                                     */
/* N = 4;      % filter order (must be even)                            */
/* F0 = 60;    % center frequency                                       */
/* Q = 8;     % quality factor                                          */
/* Dparam = fdesign.notch('N,F0,Q',N,F0/(Fs/2),Q);                      */
/* HN = design(Dparam,'FilterStructure','df1sos','SystemObject',true);  */
/* sosMatrix = HN.SOSMatrix;                                            */
/* sclValues = HN.ScaleValues;                                          */
/* b = repmat(sclValues(1:end-1),1,3).*sosMatrix(:,(1:3));              */
/* a = sosMatrix(:,(5:6));                                              */
/* %% Quantize coefficients:                                            */
/* QC = 31; % number of fractional bits in coefficients                 */
/* b = int32(b*2^(QC-1));                                               */
/* a = int32(a*2^(QC-1));                                               */
/************************************************************************/
int Notch_filter_IIR(int index, int new_data)
{
    /* Notch filter coefficients */
    int i;
    int x;
    int y;
    long long yM;

    x = new_data; // new data becomes input to first stage
    for(i = 0; i < NOTCH_N; i++)
    {
        // Output of biquad stage i:
        yM = (long long)instance[index].b_notch[i][0]*x + instance[index].s_notch[i][0];
        y = (int) (yM>>(NOTCH_Q-1));
    
        // Update internal states of stage i
        instance[index].s_notch[i][0] = (long long) instance[index].b_notch[i][1]*x - (long long)instance[index].a_notch[i][0]*y + instance[index].s_notch[i][1];
        instance[index].s_notch[i][1] = (long long) instance[index].b_notch[i][2]*x - (long long)instance[index].a_notch[i][1]*y;
    
        // output of this stage becomes input to next stage
        x = y;
    }   
    
    return(y);
}

//////////////////////////////////////////////
//      Integral High Pass Filter           //
//       By Hai Tang, 2015.9.11             //
//////////////////////////////////////////////
int Integral_High_Pass_Filter(int index, int new_data)
{
    int output = 0;

    if(index < MAX_ELECTRODES)
    { 
        output = new_data - instance[index].integral;
        instance[index].integral = instance[index].integral + (instance[index].resultPrev + ((output - instance[index].resultPrev)>>1))>>3; 
        instance[index].resultPrev = output;
    }

    return output;
}

/*                      */
/*  Public Functions    */
/*                      */

void Filter_init()
{
    for(int i = 0; i < MAX_ELECTRODES; i++)
    {
        /* Variables to implement the high pass filter */
        instance[i].prev_result = 0; // y[n-1]]
        instance[i].hpf_input_prev = 0; // x[n-1]]

        /* Variables used to implement the notch filter */
        memset(instance[i].s_notch, 0, sizeof(instance[i].s_notch)*2*NOTCH_N);
		
		//set if 0 for 50Hz notch and if 1 for 60Hz notch 
		#if 0 //60Hz coefficient
			instance[i].b_notch[0][0] = 1056000713;
			instance[i].b_notch[0][1] = -1963688804;
			instance[i].b_notch[0][2] = 1056000361;
			instance[i].b_notch[1][0] = 1056000713;
			instance[i].b_notch[1][1] = -1963689070;
			instance[i].b_notch[1][2] = 1056000361;
			instance[i].a_notch[0][0] = -1949090498;
			instance[i].a_notch[0][1] = 1037096788;
			instance[i].a_notch[1][0] = -1977759923;
			instance[i].a_notch[1][1] = 1040010350;
		#else //50Hz
			instance[i].b_notch[0][0] = 1058937104;
			instance[i].b_notch[0][1] = -2014217685;
			instance[i].b_notch[0][2] = 1058936814;
			instance[i].b_notch[1][0] = 1058937104;
			instance[i].b_notch[1][1] = -2014217889;
			instance[i].b_notch[1][2] = 1058936806;
			instance[i].a_notch[0][0] = -2003745162;
			instance[i].a_notch[0][1] = 1043097568;
			instance[i].a_notch[1][0] = -2024312659;
			instance[i].a_notch[1][1] = 1045576501;
		#endif
        instance[i].integral = 0;
        instance[i].resultPrev = 0;
    }
}


int Filter_process_sensor_input(int index, int emg_data)
{
    int result = 0;
    // 1st apply 1st order high pass filter
    // to remove DC offset and baseline drift
    result = HighPass_filter_IIR(emg_data, instance[index].hpf_input_prev, instance[index].prev_result);

    result = Integral_High_Pass_Filter(index, result);

    // Check for overflow, if so saturate result:
    if(result>MAX_ADS_OUT)
        result=MAX_ADS_OUT;
    else if(result<MIN_ADS_OUT)
        result=MIN_ADS_OUT;
    instance[index].hpf_input_prev = emg_data;
    instance[index].prev_result = result;

    // apply 4th order notch filter to remove 60 Hz
    result = Notch_filter_IIR(index, result);

    // Check for overflow:
    if(result>MAX_ADS_OUT)
        result=MAX_ADS_OUT;
    else if(result<MIN_ADS_OUT)
        result=MIN_ADS_OUT;
    
    return result;
}
#if 0
int Filter_process_DAC_output(int index, int emg_data)
{
    /////////////////////////////////////////////////
    //      Cut off Abnormal Large Spike on Raw    //
    //          By Hai Tang, 2015.9.2              //
    /////////////////////////////////////////////////
    //Removes spikes and limits the output range to amplitude of human EMG
    if(emg_data > SPIKE_CUTOFF_MAX){
        emg_data = SPIKE_CUTOFF_MAX; //cutoff the spike
    }
    if(emg_data < SPIKE_CUTOFF_MIN){
        emg_data = SPIKE_CUTOFF_MIN;
    }

    //////////////////////////////////////////
    // Convert Raw Data to Envelop          //
    // By Hai Tang, 2015.7.22               //
    //////////////////////////////////////////
    if(id<WindowLength){//Fill the window
        window[id] = result;
        id++;
    }
    else if(id>=WindowLength){
        envelop = 0;//clear previous envelop value
        //Take the RMS window
        for(i=0; i<WindowLength; i++){
            envelop += window[i]*window[i]/WindowLength;// square, mean, put mean here to avoid data overflow
        }
        envelop = sqrt(envelop);// root

       //Shift the window forward 1 step
        for(i=0; i<WindowLength-1; i++){
            window[i] = window[i+1];
        }
        window[WindowLength-1] = result;

    }

    ////////////////////////////////////////////////////
    //   Shift Down and Cut Negative Part of Envelop  //
    //            By Hai Tang, 2015.9.2               //
    ////////////////////////////////////////////////////
    envelop -= baselineThresh;
    if(envelop<0){
        envelop=0;
    }
    
    //////////////////////////////////////////
    //     Rescale the envelop to 0-255     //
    //     Which corresponding to 0-3.3V    //
    //          By Hai Tang, 2015.8.10      //
    //////////////////////////////////////////
    DACenvelop = envelop*255/(envelopPeak-baselineThresh);//D2 envelop peaks at 1400 with gain 1. Normalize DACenvelop to 0-255
    if(DACenvelop>255){
        DACenvelop = 255;//For DACenvelop>255, make it 255, otherwise it will become DACenvelop-255 as default
    }
    //update the DAC output buffer for all electrodes
  //  unsigned char DAC_WRITE_BUF_on[8] = {DACenvelop,DACenvelop,0,0,0,0,0,0};
    //output to DAC
 //   DAC_Output(0b00000011, DAC_WRITE_BUF_on);

}
#endif
