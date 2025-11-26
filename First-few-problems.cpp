#include <iostream>

using namespace std;

int main(){

    /* A
    long long N, sum = 0;
    cin >> N;
    long long arr[N];
    for (int i = 0; i < N; i++){
        cin >> arr[i];
        sum += arr[i];
    }
    if(sum<0)
        cout << -sum;
    else
    cout << sum; */

    /* E
    long long N, lowest, pose;
    cin >> N;
    int arr[N];
    for (int i = 0; i < N;i++)
    {
        cin >> arr[i];
    }
    lowest = arr[0];
    pose = 1;
    for (int i = 1; i < N;i++){
        if (arr[i] < lowest)
        {
            lowest = arr[i];
            pose = i + 1;
        }
    }
    cout << lowest <<" "<< pose; */

    int A, B;
    string ch;
}